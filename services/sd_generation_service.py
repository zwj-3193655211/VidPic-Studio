"""
Stable Diffusion Generation Service - multi-model support
"""

import json
import logging
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

import torch
from PIL import Image

try:
    from diffusers import (
        StableDiffusionPipeline,
        StableDiffusionXLPipeline,
        DPMSolverMultistepScheduler,
    )
except ImportError:
    StableDiffusionPipeline = None
    StableDiffusionXLPipeline = None
    DPMSolverMultistepScheduler = None

logger = logging.getLogger(__name__)


class SDGenerationService:
    """Service for generating images using Stable Diffusion (SD1.5 / SDXL / single-file checkpoints)"""

    def __init__(
        self,
        model_name: str = "runwayml/stable-diffusion-v1-5",
        model_type: str = "diffusers",
        base_dir: str = None,
        width: int = 512,
        height: int = 512,
        device: str = None,
        use_float16: bool = True,
        enable_attention_slicing: bool = True
    ):
        """
        Initialize SD Generation Service

        Args:
            model_name: HuggingFace model ID, local diffusers dir, or single-file checkpoint path
            model_type: "diffusers" (dir/repo-id) or "sdxl_single_file" (SDXL ckpt + base_dir)
            base_dir: SDXL base components dir (required for sdxl_single_file)
            width: Default image width
            height: Default image height
            device: Device to use ('cuda', 'cpu', or None for auto)
            use_float16: Whether to use float16 precision (faster, less memory)
            enable_attention_slicing: Whether to enable attention slicing (saves memory)
        """
        if StableDiffusionPipeline is None:
            raise ImportError(
                "diffusers is not installed. "
                "Install with: pip install diffusers transformers accelerate"
            )

        self.model_name = model_name
        self.model_type = model_type
        self.base_dir = base_dir
        self.width = width
        self.height = height

        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.use_float16 = use_float16 and self.device == "cuda"
        self.enable_attention_slicing = enable_attention_slicing

        # Pipeline (loaded lazily)
        self.pipeline = None
        self.model_loaded = False

        logger.info(f"Initialized SDGenerationService with model: {model_name} (type={model_type})")
        logger.info(f"Device: {self.device}, Float16: {self.use_float16}")

    # ------------------------------------------------------------------ #
    # Model loading
    # ------------------------------------------------------------------ #
    @staticmethod
    def _has_fp16_variants(model_dir: str) -> bool:
        """True if the dir contains *.fp16.safetensors variant files"""
        base = Path(model_dir)
        if not base.is_dir():
            return False
        return any(p.name.endswith(".fp16.safetensors") for p in base.rglob("*"))

    def _detect_pipeline_class(self, model_dir: str):
        """Read model_index.json to pick the right pipeline class"""
        index_path = Path(model_dir) / "model_index.json"
        if index_path.exists():
            try:
                idx = json.loads(index_path.read_text(encoding="utf-8"))
                class_name = idx.get("_class_name", "")
                if "XL" in class_name:
                    return StableDiffusionXLPipeline
            except Exception:
                pass
        return StableDiffusionPipeline

    def load_model(self):
        """Load the model (lazy: only when first generation is requested)"""
        if self.model_loaded:
            logger.info("Model already loaded")
            return

        logger.info(f"Loading model: {self.model_name}...")
        try:
            if self.model_type == "sdxl_single_file":
                self.pipeline = self._load_sdxl_single_file()
            else:
                self.pipeline = self._load_diffusers_dir()

            # Use a faster scheduler
            self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipeline.scheduler.config
            )

            self._apply_memory_opts()

            if not getattr(self, "model_offloaded", False):
                self.pipeline = self.pipeline.to(self.device)
            self.model_loaded = True
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise

    def _apply_memory_opts(self):
        """Memory optimizations for 8GB-class GPUs"""
        if isinstance(self.pipeline, StableDiffusionXLPipeline):
            try:
                self.pipeline.enable_vae_tiling()
            except Exception:
                pass
            # VAE must stay in float32 to avoid the "modules should be kept in
            # float32" warning and eliminate possible colour-banding artefacts.
            # The VAE is only ~167 MB so this has negligible VRAM impact.
            try:
                self.pipeline.vae.to(dtype=torch.float32)
            except Exception:
                pass
            if self.enable_attention_slicing:
                try:
                    self.pipeline.enable_model_cpu_offload()
                    self.model_offloaded = True
                except Exception as e:
                    logger.warning(f"model_cpu_offload unavailable: {e}")
        elif self.enable_attention_slicing:
            self.pipeline.enable_attention_slicing()

    def _load_diffusers_dir(self):
        """Load from a diffusers directory or repo id"""
        model_name = self.model_name
        dtype = torch.float16 if self.use_float16 else torch.float32

        # If it's a local directory, auto-detect the pipeline class and fp16 variants
        if Path(model_name).is_dir() and (Path(model_name) / "model_index.json").exists():
            pipeline_cls = self._detect_pipeline_class(model_name)
            kwargs = dict(
                torch_dtype=dtype,
                safety_checker=None,
                requires_safety_checker=False,
            )
            if self.use_float16 and self._has_fp16_variants(model_name):
                kwargs["variant"] = "fp16"
            return pipeline_cls.from_pretrained(model_name, **kwargs)

        # Fallback: classic SD1.5 pipeline (repo id or other local dir)
        return StableDiffusionPipeline.from_pretrained(
            model_name,
            torch_dtype=dtype,
            safety_checker=None,
            requires_safety_checker=False
        )

    def _load_sdxl_single_file(self):
        """
        Load an SDXL single-file checkpoint using a LOCAL diffusers base dir as
        the architecture config (fully offline; diffusers does the LDM->diffusers
        conversion internally).
        """
        if not self.base_dir or not Path(self.base_dir).is_dir():
            raise FileNotFoundError(
                f"SDXL base components dir not found: {self.base_dir}. "
                "Download with: snapshot_download('AI-ModelScope/stable-diffusion-xl-base-1.0', ...)"
            )
        if not Path(self.model_name).is_file():
            raise FileNotFoundError(f"SDXL checkpoint not found: {self.model_name}")

        dtype = torch.float16 if self.use_float16 else torch.float32
        return StableDiffusionXLPipeline.from_single_file(
            self.model_name,
            torch_dtype=dtype,
            config=self.base_dir,        # local diffusers repo with architecture configs
            local_files_only=True,       # never touch the network
            safety_checker=None,
            requires_safety_checker=False,
        )

    def unload_model(self):
        """Unload the model to free memory"""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            self.model_loaded = False

            if self.device == "cuda":
                torch.cuda.empty_cache()

            logger.info("Model unloaded from memory")

    # ------------------------------------------------------------------ #
    # Generation
    # ------------------------------------------------------------------ #
    def generate_single(
        self,
        prompt: str,
        negative_prompt: str = "",
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        width: int = None,
        height: int = None,
        seed: int = None,
        output_dir: str = None,
        save_image: bool = True
    ) -> Image.Image:
        """Generate a single image"""
        if not self.model_loaded:
            self.load_model()

        width = width or self.width
        height = height or self.height
        logger.info(f"Generating image with prompt: {prompt} ({width}x{height}, {num_inference_steps} steps)")

        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        with torch.inference_mode():
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt or None,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                generator=generator
            )
        image = result.images[0]

        if save_image and output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            path = Path(output_dir) / f"image_{datetime.now().strftime('%H%M%S')}.png"
            image.save(path)
            logger.info(f"Saved image to: {path}")

        return image

    def generate_batch(
        self,
        prompt: str,
        num_images: int = 4,
        negative_prompt: str = "",
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        width: int = None,
        height: int = None,
        output_dir: str = None
    ) -> Tuple[List[Image.Image], Dict[str, Any]]:
        """Generate a batch of images with the same prompt"""
        logger.info(f"Generating batch of {num_images} images")

        width = width or self.width
        height = height or self.height

        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        batch_dir = None
        if output_dir:
            batch_dir = Path(output_dir) / batch_id
            batch_dir.mkdir(parents=True, exist_ok=True)

        images = []
        for i in range(num_images):
            logger.info(f"Generating image {i+1}/{num_images}")
            image = self.generate_single(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                output_dir=str(batch_dir) if batch_dir else None,
                save_image=(batch_dir is not None)
            )
            images.append(image)

        metadata = {
            "batch_id": batch_id,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_images": num_images,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "width": width,
            "height": height,
            "device": self.device,
            "model_name": self.model_name,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Generated {len(images)} images in batch {batch_id}")
        return images, metadata
