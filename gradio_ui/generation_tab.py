"""
Generation Tab for Gradio UI - multi-model with per-model parameter adaptation
"""

import logging
from pathlib import Path
from typing import List, Tuple

try:
    import gradio as gr
except ImportError:
    gr = None

from services.generation_service import GenerationService
from models_registry import available_models, get_model

logger = logging.getLogger(__name__)


class GenerationTab:
    """Generation tab for Gradio interface"""

    def __init__(
        self,
        generation_service: GenerationService,
        default_output_dir: str = "output"
    ):
        """
        Initialize generation tab

        Args:
            generation_service: Service for generating images
            default_output_dir: Default output directory
        """
        self.generation_service = generation_service
        self.default_output_dir = Path(default_output_dir)

        # Ensure output directory exists
        self.default_output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def build(self) -> gr.Tab:
        """Build the generation tab"""
        if gr is None:
            raise ImportError("Gradio is not installed. Install with: pip install gradio")

        with gr.Tab("图片生成") as tab:
            gr.Markdown("## 图片生成")

            # Model selector
            with gr.Row():
                model_dropdown = gr.Dropdown(
                    choices=list(available_models().keys()),
                    value=self.generation_service.model_key,
                    label="模型",
                    info="切换模型后，下方参数会自动适配该模型的推荐值"
                )

            model_info = gr.Markdown(self._model_info_text(self.generation_service.model_key))

            # Prompt inputs
            with gr.Row():
                prompt_input = gr.Textbox(
                    label="生成提示词",
                    placeholder="例如：一位年轻女性的肖像，自然光照",
                    lines=3
                )

            with gr.Row():
                negative_prompt_input = gr.Textbox(
                    label="负面提示词",
                    placeholder="可选，描述不想要的内容",
                    lines=2
                )

            # Reference image (img2img)
            with gr.Row():
                ref_image_input = gr.Image(
                    label="参考图（图生图，可选）",
                    type="pil",
                    sources=["upload", "clipboard"],
                    info="上传图片后按参考图构图/风格生成；留空则为纯文生图",
                )
                strength_input = gr.Slider(
                    minimum=0.1, maximum=1.0, value=0.75, step=0.05,
                    label="参考强度",
                    info="0.1≈几乎保留原图，1.0≈完全重绘"
                )

            # Parameter row (values/ranges adapt per model)
            with gr.Row():
                num_images = gr.Slider(
                    minimum=1, maximum=10, value=4, step=1, label="生成数量"
                )
                guidance_scale = gr.Slider(
                    minimum=1.0, maximum=20.0, value=7.5, step=0.5, label="引导系数"
                )
                num_inference_steps = gr.Slider(
                    minimum=5, maximum=100, value=30, step=5, label="推理步数"
                )
                size_dropdown = gr.Dropdown(
                    choices=["512x512"], value="512x512", label="分辨率"
                )

            with gr.Row():
                output_dir_input = gr.Textbox(
                    value=str(self.default_output_dir),
                    label="输出目录"
                )

            # Action buttons
            with gr.Row():
                generate_btn = gr.Button("生成图片", variant="primary")

            # Status output
            with gr.Row():
                status_output = gr.Textbox(
                    label="状态",
                    interactive=False,
                    lines=3
                )

            # Gallery output
            with gr.Row():
                gallery_output = gr.Gallery(
                    label="生成的图片",
                    columns=4,
                    height=400
                )

            # Wire up events
            model_dropdown.change(
                fn=self.on_model_change,
                inputs=[model_dropdown],
                outputs=[
                    model_info,
                    negative_prompt_input,
                    num_images,
                    guidance_scale,
                    num_inference_steps,
                    size_dropdown,
                ]
            )
            generate_btn.click(
                fn=self.generate_images,
                inputs=[
                    model_dropdown,
                    prompt_input,
                    negative_prompt_input,
                    num_images,
                    guidance_scale,
                    num_inference_steps,
                    size_dropdown,
                    output_dir_input,
                    ref_image_input,
                    strength_input,
                ],
                outputs=[gallery_output, status_output]
            )

        return tab

    def _model_info_text(self, model_key: str) -> str:
        """Markdown summary shown above the parameter controls"""
        spec = get_model(model_key)
        return (
            f"**当前模型：{spec['name']}** ｜ "
            f"类型: {spec['type']} ｜ "
            f"推荐分辨率: {spec['size_default']} ｜ "
            f"推荐步数: {spec['steps_default']} ｜ "
            f"推荐引导系数: {spec['guidance_default']}"
        )

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #
    def on_model_change(self, model_key: str):
        """
        Adapt parameter controls to the selected model

        Returns:
            Tuple of gr.update() values for model_info, negative_prompt,
            num_images, guidance_scale, num_inference_steps, size_dropdown
        """
        spec = get_model(model_key)
        size_choices = [c[0] for c in spec["size_choices"]]
        s_min, s_max, s_step = spec["steps_range"]
        g_min, g_max, g_step = spec["guidance_range"]

        return (
            self._model_info_text(model_key),
            gr.update(value=spec["negative_prompt_default"]),
            gr.update(value=spec["num_images_default"]),
            gr.update(value=spec["guidance_default"], minimum=g_min, maximum=g_max, step=g_step),
            gr.update(value=spec["steps_default"], minimum=s_min, maximum=s_max, step=s_step),
            gr.update(choices=size_choices, value=spec["size_default"]),
        )

    def generate_images(
        self,
        model_key: str,
        prompt: str,
        negative_prompt: str,
        num_images: int,
        guidance_scale: float,
        num_inference_steps: int,
        size_label: str,
        output_dir: str,
        ref_image=None,
        strength: float = 0.75
    ) -> Tuple[List[Tuple[str, str]], str]:
        """Generate images with the selected model and parameters"""
        try:
            if not prompt or not prompt.strip():
                return [], "错误：请输入生成提示词"

            # Switch model if a different one was selected
            if model_key != self.generation_service.model_key:
                self.generation_service.switch_model(model_key)
                logger.info(f"Model switched to {model_key}")

            # Parse size label into width/height
            width, height = 512, 512
            for label, w, h in get_model(model_key)["size_choices"]:
                if label == size_label:
                    width, height = w, h
                    break

            logger.info(
                f"Generating {num_images} images | model={model_key} | "
                f"{width}x{height} | steps={num_inference_steps} | guidance={guidance_scale}"
                f" | img2img={ref_image is not None}"
            )
            images, metadata = self.generation_service.generate_batch(
                prompt=prompt,
                num_images=num_images,
                negative_prompt=negative_prompt or "",
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                width=width,
                height=height,
                output_dir=output_dir,
                init_image=ref_image,
                strength=strength,
            )

            if not images:
                return [], "生成失败：未能生成任何图片"

            gallery_images = [(img, f"Image {i+1}") for i, img in enumerate(images)]
            mode = "图生图" if ref_image is not None else "文生图"
            status = (
                f"成功生成 {len(images)} 张图片"
                f"（模型: {self.generation_service.get_current_model_name()}，"
                f"{mode}，{width}x{height}，{num_inference_steps} 步）"
            )
            if ref_image is not None:
                status += f"，参考强度 {strength}"
            batch_dir = metadata.get("batch_id", "")
            if batch_dir:
                status += f"，保存至 {output_dir}/{batch_dir}"

            return gallery_images, status

        except Exception as e:
            logger.error(f"Error generating images: {e}", exc_info=True)
            return [], f"错误：{str(e)}"
