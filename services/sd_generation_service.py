"""
Stable Diffusion Generation Service
"""

import logging
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime

import torch
from PIL import Image

try:
    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    from transformers import CLIPTextModel, CLIPTokenizer
except ImportError:
    StableDiffusionPipeline = None
    DPMSolverMultistepScheduler = None

logger = logging.getLogger(__name__)


class SDGenerationService:
    """Service for generating images using Stable Diffusion"""

    # Default angle modifiers for multi-angle generation
    DEFAULT_ANGLES = [
        "front view portrait, facing forward",
        "three-quarter view, slightly turned to the left",
        "profile view facing right, side portrait",
        "three-quarter view, slightly turned to the right",
        "back view, showing the back of the head",
        "looking up, slightly elevated angle",
        "looking down, slightly lowered angle",
        "tilted head, artistic pose"
    ]

    def __init__(
        self,
        model_name: str = "runwayml/stable-diffusion-v1-5",
        device: str = None,
        use_float16: bool = True,
        enable_attention_slicing: bool = True
    ):
        """
        Initialize SD Generation Service

        Args:
            model_name: HuggingFace model ID or local path
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
        # Auto-detect device if not specified
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.use_float16 = use_float16 and self.device == "cuda"
        self.enable_attention_slicing = enable_attention_slicing

        # Pipeline (loaded lazily)
        self.pipeline: Optional[StableDiffusionPipeline] = None
        self.model_loaded = False

        logger.info(f"Initialized SDGenerationService with model: {model_name}")
        logger.info(f"Device: {self.device}, Float16: {self.use_float16}")

    def load_model(self):
        """
        Load the Stable Diffusion model

        This is a lazy-loading method that downloads and loads the model
        only when needed.
        """
        if self.model_loaded:
            logger.info("Model already loaded")
            return

        logger.info(f"Loading model: {self.model_name}...")

        try:
            # Load model
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.use_float16 else torch.float32,
                safety_checker=None,  # Disable safety checker for speed
                requires_safety_checker=False
            )

            # Use better scheduler
            self.pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipeline.scheduler.config
            )

            # Enable memory optimizations
            if self.enable_attention_slicing:
                self.pipeline.enable_attention_slicing()

            # Move to device
            self.pipeline = self.pipeline.to(self.device)

            # Enable memory-efficient attention if available
            if hasattr(self.pipeline, "enable_xformers_memory_efficient_attention"):
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                    logger.info("Enabled xformers memory efficient attention")
                except Exception:
                    logger.info("xformers not available, using default attention")

            self.model_loaded = True
            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise

    def generate_single(
        self,
        prompt: str,
        negative_prompt: str = "",
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        width: int = 512,
        height: int = 512,
        seed: int = None,
        output_dir: str = None,
        save_image: bool = True
    ) -> Image.Image:
        """
        Generate a single image

        Args:
            prompt: Text prompt for generation
            negative_prompt: Negative prompt to avoid certain features
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale for generation
            width: Image width
            height: Image height
            seed: Random seed for reproducibility
            output_dir: Directory to save the image
            save_image: Whether to save the image to disk

        Returns:
            Generated PIL Image
        """
        if not self.model_loaded:
            self.load_model()

        logger.info(f"Generating image with prompt: {prompt}")

        # Set seed if specified
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)

        # Generate image
        with torch.inference_mode():
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                generator=generator
            )

        image = result.images[0]

        # Save image if requested
        if save_image and output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}_{uuid.uuid4().hex[:8]}.png"
            image.save(output_path / filename)
            logger.info(f"Saved image to: {output_path / filename}")

        return image

    def _generate_angle_prompts(
        self,
        base_prompt: str,
        num_angles: int = 4,
        custom_angles: List[str] = None
    ) -> List[str]:
        """
        Generate prompts for different angles

        Args:
            base_prompt: Base prompt describing the subject
            num_angles: Number of angles to generate
            custom_angles: Custom angle descriptions

        Returns:
            List of prompts with angle modifiers
        """
        if custom_angles:
            angles = custom_angles
        else:
            angles = self.DEFAULT_ANGLES[:num_angles]

        prompts = []
        for angle in angles:
            prompt = f"{base_prompt}, {angle}, high quality, detailed"
            prompts.append(prompt)

        return prompts

    def generate_multi_angle(
        self,
        base_prompt: str,
        num_angles: int = 4,
        custom_angles: List[str] = None,
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        width: int = 512,
        height: int = 512,
        output_dir: str = None
    ) -> Tuple[List[Image.Image], List[str]]:
        """
        Generate images from multiple angles

        Args:
            base_prompt: Base prompt describing the subject
            num_angles: Number of angles to generate
            custom_angles: Custom angle descriptions
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale for generation
            width: Image width
            height: Image height
            output_dir: Directory to save images

        Returns:
            Tuple of (list of images, list of prompts used)
        """
        logger.info(f"Generating {num_angles} multi-angle images")

        # Generate prompts for each angle
        prompts = self._generate_angle_prompts(
            base_prompt=base_prompt,
            num_angles=num_angles,
            custom_angles=custom_angles
        )

        # Generate images
        images = []
        for i, prompt in enumerate(prompts):
            logger.info(f"Generating angle {i+1}/{num_angles}: {prompt}")

            image = self.generate_single(
                prompt=prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                output_dir=output_dir,
                save_image=(output_dir is not None)
            )

            images.append(image)

        logger.info(f"Generated {len(images)} multi-angle images")
        return images, prompts

    def generate_batch(
        self,
        prompt: str,
        num_images: int = 4,
        negative_prompt: str = "",
        num_inference_steps: int = 50,
        guidance_scale: float = 7.5,
        width: int = 512,
        height: int = 512,
        output_dir: str = None
    ) -> Tuple[List[Image.Image], Dict[str, Any]]:
        """
        Generate a batch of images with the same prompt

        Args:
            prompt: Text prompt for generation
            num_images: Number of images to generate
            negative_prompt: Negative prompt
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale
            width: Image width
            height: Image height
            output_dir: Directory to save images

        Returns:
            Tuple of (list of images, metadata dict)
        """
        logger.info(f"Generating batch of {num_images} images")

        # Create batch ID
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Save batch directory
        batch_dir = None
        if output_dir:
            batch_dir = Path(output_dir) / batch_id
            batch_dir.mkdir(parents=True, exist_ok=True)

        # Generate images
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

        # Create metadata
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

    def unload_model(self):
        """Unload the model to free memory"""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            self.model_loaded = False

            # Clear GPU cache
            if self.device == "cuda":
                torch.cuda.empty_cache()

            logger.info("Model unloaded from memory")
