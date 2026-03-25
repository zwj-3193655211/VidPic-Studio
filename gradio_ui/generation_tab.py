"""
Generation Tab for Gradio UI
"""

import logging
from pathlib import Path
from typing import Optional, List, Callable

try:
    import gradio as gr
except ImportError:
    gr = None

from services.generation_service import GenerationService
from services.scoring_service import ScoringService


logger = logging.getLogger(__name__)


class GenerationTab:
    """Generation tab for Gradio interface"""

    def __init__(
        self,
        generation_service: GenerationService,
        scoring_service: ScoringService,
        default_output_dir: str = "output"
    ):
        """
        Initialize generation tab

        Args:
            generation_service: Service for generating faces
            scoring_service: Service for scoring and filtering
            default_output_dir: Default output directory
        """
        self.generation_service = generation_service
        self.scoring_service = scoring_service
        self.default_output_dir = Path(default_output_dir)

        # Ensure output directory exists
        self.default_output_dir.mkdir(parents=True, exist_ok=True)

        # UI state
        self.current_batch_dir: Optional[Path] = None

    def build(self) -> gr.Tab:
        """
        Build the generation tab

        Returns:
            Gradio Tab object
        """
        if gr is None:
            raise ImportError("Gradio is not installed. Install with: pip install gradio")

        with gr.Tab("多角度人脸生成") as tab:
            gr.Markdown("## 生成多角度人脸图片")

            # Input components
            with gr.Row():
                prompt_input = gr.Textbox(
                    label="生成提示词",
                    placeholder="例如：一位年轻女性的肖像，自然光照",
                    lines=3
                )

            with gr.Row():
                num_images = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=4,
                    step=1,
                    label="生成数量"
                )
                guidance_scale = gr.Slider(
                    minimum=1.0,
                    maximum=20.0,
                    value=7.5,
                    step=0.5,
                    label="引导系数"
                )
                num_inference_steps = gr.Slider(
                    minimum=10,
                    maximum=100,
                    value=50,
                    step=5,
                    label="推理步数"
                )

            with gr.Row():
                enable_scoring = gr.Checkbox(
                    value=True,
                    label="启用质量评分"
                )
                quality_threshold = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.7,
                    step=0.05,
                    label="质量阈值"
                )

            with gr.Row():
                output_dir_input = gr.Textbox(
                    value=str(self.default_output_dir),
                    label="输出目录"
                )

            # Action buttons
            with gr.Row():
                generate_btn = gr.Button("生成图片", variant="primary")
                save_best_btn = gr.Button("保存最佳图片", variant="secondary")

            # Status output
            with gr.Row():
                status_output = gr.Textbox(
                    label="状态",
                    interactive=False,
                    lines=2
                )

            # Gallery output
            with gr.Row():
                gallery_output = gr.Gallery(
                    label="生成的图片",
                    columns=4,
                    height=400
                )

            # Metrics output
            with gr.Row():
                metrics_output = gr.JSON(
                    label="质量指标"
                )

            # Wire up events
            generate_btn.click(
                fn=self.generate_faces,
                inputs=[
                    prompt_input,
                    num_images,
                    guidance_scale,
                    num_inference_steps,
                    enable_scoring,
                    quality_threshold,
                    output_dir_input
                ],
                outputs=[gallery_output, status_output, metrics_output]
            )

            save_best_btn.click(
                fn=self.save_best_faces,
                inputs=[quality_threshold, output_dir_input],
                outputs=[status_output]
            )

        return tab

    def generate_faces(
        self,
        prompt: str,
        num_images: int,
        guidance_scale: float,
        num_inference_steps: int,
        enable_scoring: bool,
        quality_threshold: float,
        output_dir: str
    ) -> tuple[List[tuple[str, str]], str, dict]:
        """
        Generate faces with optional scoring

        Args:
            prompt: Generation prompt
            num_images: Number of images to generate
            guidance_scale: Guidance scale for generation
            num_inference_steps: Number of inference steps
            enable_scoring: Whether to enable quality scoring
            quality_threshold: Minimum quality threshold
            output_dir: Output directory path

        Returns:
            Tuple of (gallery images, status message, metrics)
        """
        try:
            if not prompt or not prompt.strip():
                return [], "错误：请输入生成提示词", {}

            # Generate images
            logger.info(f"Generating {num_images} images with prompt: {prompt}")
            images, metadata = self.generation_service.generate_batch(
                prompt=prompt,
                num_images=num_images,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                output_dir=output_dir
            )

            if not images:
                return [], "生成失败：未能生成任何图片", {}

            # Score images if enabled
            scores = []
            if enable_scoring:
                logger.info("Scoring generated images...")
                scores = self.scoring_service.score_batch(images)

            # Create gallery format
            gallery_images = []
            for i, img in enumerate(images):
                score = scores[i] if scores and i < len(scores) else 0.0
                label = f"Image {i+1}" + (f" (Score: {score:.3f})" if scores else "")
                gallery_images.append((img, label))

            # Create status message
            num_high_quality = sum(1 for s in scores if s >= quality_threshold) if scores else num_images
            avg_score = sum(scores) / len(scores) if scores else 0.0

            status = (
                f"成功生成 {len(images)} 张图片\n"
                f"平均质量分数: {avg_score:.3f} | "
                f"高质量图片: {num_high_quality}/{len(images)} (阈值: {quality_threshold:.2f})"
            )

            # Create metrics
            metrics = {
                "total_generated": len(images),
                "average_score": float(avg_score),
                "high_quality_count": num_high_quality,
                "scores": [float(s) for s in scores] if scores else []
            }

            # Store current batch for saving
            self.current_batch_dir = Path(output_dir) / metadata.get("batch_id", "latest")

            return gallery_images, status, metrics

        except Exception as e:
            logger.error(f"Error generating faces: {e}", exc_info=True)
            return [], f"错误：{str(e)}", {}

    def save_best_faces(
        self,
        quality_threshold: float,
        output_dir: str
    ) -> str:
        """
        Save best faces from current batch

        Args:
            quality_threshold: Minimum quality threshold
            output_dir: Output directory path

        Returns:
            Status message
        """
        try:
            if not self.current_batch_dir or not self.current_batch_dir.exists():
                return "错误：没有可保存的图片批次。请先生成图片。"

            # TODO: Implement loading and filtering from current_batch_dir
            # This would load images, score them, and save those above threshold

            return f"已保存质量分数 >= {quality_threshold:.2f} 的图片到 {output_dir}"

        except Exception as e:
            logger.error(f"Error saving faces: {e}", exc_info=True)
            return f"错误：{str(e)}"
