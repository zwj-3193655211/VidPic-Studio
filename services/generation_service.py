"""
Generation Service - Facade for SD Generation Service
"""

import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image

from services.sd_generation_service import SDGenerationService

logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating face images (wrapper for SDGenerationService)"""

    def __init__(
        self,
        model_path: str = None,
        use_sd: bool = True,
        device: str = None
    ):
        """
        Initialize generation service

        Args:
            model_path: Path to the generation model (or HuggingFace model ID)
            use_sd: Whether to use Stable Diffusion (True) or placeholder (False)
            device: Device to use for generation
        """
        self.model_path = model_path
        self.use_sd = use_sd

        if use_sd:
            model_name = model_path or "runwayml/stable-diffusion-v1-5"
            self.sd_service = SDGenerationService(
                model_name=model_name,
                device=device
            )
        else:
            self.sd_service = None

        logger.info(f"Initialized GenerationService (SD enabled: {use_sd})")

    def generate_batch(
        self,
        prompt: str,
        num_images: int = 4,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 50,
        width: int = 512,
        height: int = 512,
        output_dir: str = "output"
    ) -> Tuple[List[Image.Image], Dict[str, Any]]:
        """
        Generate a batch of images

        Args:
            prompt: Text prompt for generation
            num_images: Number of images to generate
            guidance_scale: Guidance scale for generation
            num_inference_steps: Number of inference steps
            width: Image width
            height: Image height
            output_dir: Output directory for saved images

        Returns:
            Tuple of (list of PIL Images, metadata dict)
        """
        if self.use_sd and self.sd_service:
            # Use actual Stable Diffusion
            logger.info("Using Stable Diffusion for generation")
            return self.sd_service.generate_batch(
                prompt=prompt,
                num_images=num_images,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                output_dir=output_dir
            )
        else:
            # Placeholder implementation for testing
            logger.warning("Using placeholder generation (SD disabled)")
            return self._generate_placeholder_batch(
                prompt=prompt,
                num_images=num_images,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                output_dir=output_dir
            )

    def generate_multi_angle(
        self,
        base_prompt: str,
        num_angles: int = 4,
        custom_angles: List[str] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        width: int = 512,
        height: int = 512,
        output_dir: str = "output"
    ) -> Tuple[List[Image.Image], List[str]]:
        """
        Generate images from multiple angles

        Args:
            base_prompt: Base prompt describing the subject
            num_angles: Number of angles to generate
            custom_angles: Custom angle descriptions
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale
            width: Image width
            height: Image height
            output_dir: Output directory

        Returns:
            Tuple of (list of images, list of prompts used)
        """
        if self.use_sd and self.sd_service:
            return self.sd_service.generate_multi_angle(
                base_prompt=base_prompt,
                num_angles=num_angles,
                custom_angles=custom_angles,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                output_dir=output_dir
            )
        else:
            return self._generate_placeholder_multi_angle(
                base_prompt=base_prompt,
                num_angles=num_angles,
                custom_angles=custom_angles,
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
        images = []
        for i in range(num_images):
            # Create a simple placeholder image with different colors
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

    def _generate_placeholder_multi_angle(
        self,
        base_prompt: str,
        num_angles: int,
        custom_angles: List[str],
        output_dir: str
    ) -> Tuple[List[Image.Image], List[str]]:
        """Generate placeholder multi-angle images for testing"""
        from services.sd_generation_service import SDGenerationService

        # Generate prompts using SD service's method
        sd_service = SDGenerationService.__new__(SDGenerationService)
        prompts = sd_service._generate_angle_prompts(
            base_prompt=base_prompt,
            num_angles=num_angles,
            custom_angles=custom_angles
        )

        # Create placeholder images
        images = []
        for i, prompt in enumerate(prompts):
            color = (i * 30, 100 + i * 15, 200 - i * 10)
            img = Image.new('RGB', (512, 512), color=color)
            images.append(img)

        return images, prompts

    def load_model(self):
        """Load the generation model"""
        if self.sd_service:
            self.sd_service.load_model()

    def unload_model(self):
        """Unload the generation model to free memory"""
        if self.sd_service:
            self.sd_service.unload_model()
