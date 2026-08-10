"""
LTX-Video Generation Service - text-to-video (diffusers LTXPipeline)
"""

import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import torch
from PIL import Image

try:
    from diffusers import LTXPipeline, LTXImageToVideoPipeline
    from diffusers.utils import export_to_video
except ImportError:
    LTXPipeline = None
    LTXImageToVideoPipeline = None
    export_to_video = None

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_DIR = Path(__file__).resolve().parent.parent / "models" / "ltx_video"


class LTXVideoService:
    """Text-to-video generation with Lightricks LTX-Video (8GB-GPU friendly via offload)"""

    def __init__(self, model_dir: str = None, device: str = None):
        if LTXPipeline is None:
            raise ImportError(
                "diffusers LTXPipeline not available. Install: pip install diffusers>=0.32"
            )

        self.model_dir = str(model_dir or _DEFAULT_MODEL_DIR)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline = None
        self._i2v_pipeline = None
        self.model_loaded = False

        logger.info(f"Initialized LTXVideoService (model: {self.model_dir}, device: {self.device})")

    # ------------------------------------------------------------------ #
    # Model loading
    # ------------------------------------------------------------------ #
    def model_ready(self) -> bool:
        """True if the diffusers model directory exists locally"""
        return (Path(self.model_dir) / "model_index.json").is_file()

    def load_model(self):
        if self.model_loaded:
            return
        if not self.model_ready():
            raise FileNotFoundError(
                f"LTX-Video model not found at {self.model_dir}. "
                "Download it first (hf-mirror): "
                "snapshot_download('Lightricks/LTX-Video', local_dir=models/ltx_video)"
            )

        # transformers 4.57+ uses lazy module loading – diffusers can't
        # resolve T5Tokenizer from the lazy placeholder, so force-load the
        # real class and swap it into the 'transformers' namespace.
        import transformers
        from transformers.models.t5.tokenization_t5 import T5Tokenizer as _RealT5Tokenizer
        setattr(transformers, "T5Tokenizer", _RealT5Tokenizer)

        logger.info(f"Loading LTX-Video model from {self.model_dir} ...")
        self.pipeline = LTXPipeline.from_pretrained(
            self.model_dir,
            torch_dtype=torch.float16,
            safety_checker=None,
            requires_safety_checker=False,
        )
        # 8GB GPU: keep weights in RAM, stream modules to GPU when needed
        self.pipeline.enable_model_cpu_offload()
        self._i2v_pipeline = None
        self.model_loaded = True
        logger.info("LTX-Video model loaded (float16 + cpu offload)")

    def unload_model(self):
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            self._i2v_pipeline = None
            self.model_loaded = False
            if self.device == "cuda":
                torch.cuda.empty_cache()
            logger.info("LTX-Video model unloaded")

    # ------------------------------------------------------------------ #
    # Generation
    # ------------------------------------------------------------------ #
    def _get_i2v_pipeline(self):
        """Lazily build the image-to-video pipeline from the loaded T2V pipeline.
        Shares model weights via `from_pipe` (zero extra VRAM, no reload)."""
        if self._i2v_pipeline is not None:
            return self._i2v_pipeline
        self._i2v_pipeline = LTXImageToVideoPipeline.from_pipe(self.pipeline)
        logger.info("LTXImageToVideoPipeline wrapper created (shared components)")
        return self._i2v_pipeline

    def generate_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        height: int = 512,
        width: int = 768,
        num_frames: int = 97,
        num_inference_steps: int = 40,
        guidance_scale: float = 3.0,
        seed: int = None,
        init_image: Image.Image = None,
        output_dir: str = None,
        save: bool = True,
    ) -> Dict[str, Any]:
        """Generate a short video.

        If `init_image` is provided, runs image-to-video with the reference
        as the starting frame. Returns metadata dict with 'mp4_path' (if saved),
        'frames', 'fps' and 'duration_seconds'.
        """
        if not self.model_loaded:
            self.load_model()

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        logger.info(
            f"Generating video: {prompt[:80]}... | {width}x{height} | "
            f"{num_frames} frames | {num_inference_steps} steps | guidance={guidance_scale}"
            f" | mode={'I2V' if init_image is not None else 'T2V'}"
        )

        with torch.inference_mode():
            if init_image is not None:
                pipe = self._get_i2v_pipeline()
                result = pipe(
                    image=init_image,
                    prompt=prompt,
                    negative_prompt=negative_prompt or None,
                    height=height,
                    width=width,
                    num_frames=num_frames,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                )
            else:
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative_prompt or None,
                    height=height,
                    width=width,
                    num_frames=num_frames,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator,
                )

        frames: List[Image.Image] = result.frames[0]
        fps = getattr(result, "fps", 25)
        if fps is None:
            fps = 25

        metadata = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_frames": len(frames),
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "fps": fps,
            "duration_seconds": round(len(frames) / fps, 2),
            "device": self.device,
            "model": "LTX-Video",
            "timestamp": datetime.now().isoformat(),
            "frames": frames,
            "mp4_path": None,
        }

        if save and output_dir and export_to_video is not None:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            vid_id = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            mp4 = out_dir / f"{vid_id}.mp4"
            export_to_video(frames, str(mp4), fps=fps)
            metadata["mp4_path"] = str(mp4)
            logger.info(f"Video saved to: {mp4}")

        return metadata
