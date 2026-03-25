"""
Demo script for Stable Diffusion Generation

This script demonstrates how to use the SDGenerationService to generate images.
It will download the model on first run (several GBs).
"""

import logging
from pathlib import Path

from services.sd_generation_service import SDGenerationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_single_generation():
    """Demo: Generate a single image"""
    logger.info("=" * 60)
    logger.info("Demo 1: Single Image Generation")
    logger.info("=" * 60)

    service = SDGenerationService()
    service.load_model()

    image = service.generate_single(
        prompt="a portrait of a young woman with long hair, natural lighting, high quality",
        num_inference_steps=30,  # Faster for demo
        guidance_scale=7.5,
        output_dir="output/demo"
    )

    logger.info(f"Generated image size: {image.size}")
    image.save("output/demo/single_demo.png")
    logger.info("Saved image to: output/demo/single_demo.png")


def demo_multi_angle():
    """Demo: Generate multi-angle images"""
    logger.info("=" * 60)
    logger.info("Demo 2: Multi-Angle Generation")
    logger.info("=" * 60)

    service = SDGenerationService()
    # Only load model once
    if not service.model_loaded:
        service.load_model()

    custom_angles = [
        "front view portrait, facing forward",
        "three-quarter view, slightly turned to the left",
        "profile view facing right, side portrait",
        "three-quarter view, slightly turned to the right"
    ]

    images, prompts = service.generate_multi_angle(
        base_prompt="a professional portrait of a woman",
        custom_angles=custom_angles,
        num_inference_steps=25,  # Faster for demo
        guidance_scale=7.5,
        output_dir="output/demo/multi_angle"
    )

    logger.info(f"Generated {len(images)} multi-angle images")
    for i, (img, prompt) in enumerate(zip(images, prompts)):
        logger.info(f"  Angle {i+1}: {prompt[:60]}...")
        img.save(f"output/demo/multi_angle/angle_{i+1}.png")


def demo_batch_generation():
    """Demo: Generate a batch of images"""
    logger.info("=" * 60)
    logger.info("Demo 3: Batch Generation")
    logger.info("=" * 60)

    service = SDGenerationService()
    if not service.model_loaded:
        service.load_model()

    images, metadata = service.generate_batch(
        prompt="a creative portrait, artistic style, vibrant colors",
        num_images=3,
        num_inference_steps=25,
        guidance_scale=8.0,
        output_dir="output/demo/batch"
    )

    logger.info(f"Generated {len(images)} images in batch {metadata['batch_id']}")
    logger.info(f"Metadata: {metadata}")


def demo_quick_test():
    """Demo: Quick test without downloading large model"""
    logger.info("=" * 60)
    logger.info("Demo 0: Quick Test (No Model Download)")
    logger.info("=" * 60)

    service = SDGenerationService()
    logger.info(f"Service initialized with model: {service.model_name}")
    logger.info(f"Device: {service.device}")
    logger.info(f"Model loaded: {service.model_loaded}")

    # Test angle prompt generation (doesn't need model)
    prompts = service._generate_angle_prompts(
        base_prompt="a young woman",
        num_angles=4
    )

    logger.info("Generated angle prompts:")
    for i, prompt in enumerate(prompts, 1):
        logger.info(f"  {i}. {prompt}")

    logger.info("Quick test completed successfully!")
    logger.info("Note: Model will be downloaded when you call load_model()")


def main():
    """Main demo function"""
    print("\n" + "=" * 60)
    print("Stable Diffusion Generation Demo")
    print("=" * 60)
    print("\nThis demo will:")
    print("1. Run quick tests (no download)")
    print("2. Download the Stable Diffusion model (~5GB) on first run")
    print("3. Generate sample images")
    print("\nNote: First run will download several GBs of model data.")
    print("Press Ctrl+C to cancel at any time.\n")

    # Create output directory
    Path("output/demo").mkdir(parents=True, exist_ok=True)

    try:
        # Run quick test first
        demo_quick_test()

        print("\n" + "-" * 60)
        response = input("Continue with model download and image generation? (y/n): ")

        if response.lower() == 'y':
            # Uncomment the demos you want to run:

            # Demo 1: Single image
            # demo_single_generation()

            # Demo 2: Multi-angle generation
            # demo_multi_angle()

            # Demo 3: Batch generation
            # demo_batch_generation()

            logger.info("Note: Uncomment the demo functions you want to run in main()")
            logger.info("By default, only quick test runs to avoid large downloads.")
        else:
            logger.info("Skipping model download and generation demos")

    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
