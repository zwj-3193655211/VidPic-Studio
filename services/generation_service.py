"""
Generation Service - Facade for SD Generation Service
"""

import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image

from services.sd_generation_service import SDGenerationService
from models_registry import get_model, available_models, DEFAULT_MODEL

logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating images (wrapper for SDGenerationService, model-switchable)"""

    def __init__(
        self,
        model_key: str = None,
        model_path: str = None,
        use_sd: bool = True,
        device: str = None
    ):
        """
        Initialize generation service

        Args:
            model_key: Key into the model registry (defaults to DEFAULT_MODEL)
            model_path: Optional override path (replaces the registry path)
            use_sd: Whether to use Stable Diffusion (True) or placeholder (False)
            device: Device to use for generation
        """
        self.model_key = model_key or DEFAULT_MODEL
        self.model_path = model_path
        self.use_sd = use_sd
        self.sd_service = None

        if use_sd:
            self._init_sd_service(device, model_path_override=self.model_path)

        logger.info(f"Initialized GenerationService (SD enabled: {use_sd}, model: {self.model_key})")

    def _init_sd_service(self, device: str = None, model_path_override: str = None):
        """(Re)create the SD service from the current model spec.

        model_path_override is used ONLY for the initial model (e.g. --model-path
        from the launcher); switching models always uses the registry path.
        """
        spec = get_model(self.model_key)
        model_name = model_path_override if model_path_override is not None else spec["path"]

        # Default dims from the spec's default size choice
        w = h = None
        for label, w_, h_ in spec["size_choices"]:
            if label == spec["size_default"]:
                w, h = w_, h_
                break
        if w is None:
            w, h = spec["size_choices"][0][1], spec["size_choices"][0][2]

        self.sd_service = SDGenerationService(
            model_name=model_name,
            model_type=spec["type"],
            base_dir=spec.get("base_dir"),
            width=w,
            height=h,
            device=device
        )

    def switch_model(self, model_key: str, device: str = None) -> str:
        """
        Switch the active model (unloads current, next generate reloads)

        Returns:
            Display name of the newly selected model
        """
        if model_key not in available_models():
            raise KeyError(f"未知模型: {model_key}")
        if model_key == self.model_key and self.sd_service is not None:
            return available_models()[model_key]

        # Unload current model to free VRAM
        if self.sd_service is not None:
            self.sd_service.unload_model()

        self.model_key = model_key
        # NOTE: no model_path_override here — switched models always use the registry path
        self._init_sd_service(device)
        logger.info(f"Switched model to: {model_key}")
        return available_models()[model_key]

    def get_current_model_name(self) -> str:
        """Return the display name of the current model"""
        return available_models().get(self.model_key, self.model_key)

    def generate_batch(
        self,
        prompt: str,
        num_images: int = 4,
        negative_prompt: str = "",
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30,
        width: int = None,
        height: int = None,
        output_dir: str = "output"
    ) -> Tuple[List[Image.Image], Dict[str, Any]]:
        """Generate a batch of images"""
        if self.use_sd and self.sd_service:
            return self.sd_service.generate_batch(
                prompt=prompt,
                num_images=num_images,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                output_dir=output_dir
            )
        return self._generate_placeholder_batch(
            prompt=prompt,
            num_images=num_images,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            output_dir=output_dir
        )

    def _generate_placeholder_batch(
        self,
        prompt: str,
        num_images: int,
        guidance_scale: float,
        num_inference_steps: int,
        output_dir: str
    ) -> Tuple[List[Image.Image], Dict[str, Any]]:
        """Generate placeholder images for testing"""
        logger.warning("Using placeholder generation (SD disabled)")
        images = []
        for i in range(num_images):
            color = (i * 40, 100 + i * 20, 150 + i * 10)
            img = Image.new('RGB', (512, 512), color=color)
            images.append(img)

        metadata = {
            "batch_id": "placeholder_batch",
            "prompt": prompt,
            "num_images": num_images,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
            "placeholder": True
        }
        return images, metadata

    def load_model(self):
        """Load the generation model"""
        if self.sd_service:
            self.sd_service.load_model()

    def unload_model(self):
        """Unload the generation model to free memory"""
        if self.sd_service:
            self.sd_service.unload_model()
