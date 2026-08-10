"""
Video Generation Tab for Gradio UI - LTX-Video (text-to-video)
"""

import logging
from typing import Tuple

try:
    import gradio as gr
except ImportError:
    gr = None

from services.ltx_video_service import LTXVideoService

logger = logging.getLogger(__name__)

# (label, width, height)
SIZE_CHOICES = [
    ("512x512", 512, 512),
    ("768x512", 768, 512),
    ("512x768", 512, 768),
]
# (label, frames, approx seconds at 25fps)
FRAMES_CHOICES = [
    ("约 2 秒 (49 帧)", 49),
    ("约 4 秒 (97 帧)", 97),
    ("约 5 秒 (121 帧，⚠ 8GB卡易爆显存)", 121),
]


class VideoGenerationTab:
    """Video generation tab"""

    def __init__(
        self,
        video_service: LTXVideoService,
        default_output_dir: str = "output",
        on_before_generate=None,
    ):
        self.video_service = video_service
        self.default_output_dir = default_output_dir
        self.on_before_generate = on_before_generate  # called before generation (e.g. unload SD)

    def build(self) -> gr.Tab:
        if gr is None:
            raise ImportError("Gradio is not installed")

        with gr.Tab("🎬 视频生成") as tab:
            gr.Markdown(
                "## 视频生成（LTX-Video 2B）\n"
                "输入提示词生成短视频。建议英文提示词。"
                "8GB 显卡生成约 4 秒视频需要 **10-30 分钟**，生成期间 GPU 满载。"
            )

            with gr.Row():
                prompt_input = gr.Textbox(
                    label="视频提示词",
                    placeholder="例如：a cute cat walking in a sunny garden, cinematic",
                    lines=3,
                    info="描述画面内容、动作和风格，越具体越好（建议英文，效果最佳）",
                )

            with gr.Row():
                negative_prompt_input = gr.Textbox(
                    label="负面提示词",
                    placeholder="可选",
                    lines=1,
                    info="不想要的内容，如：blurry, low quality, distorted",
                )

            # Reference image (image-to-video) — coming soon
            # (I2V via from_pipe has a known diffusers 0.39 + cpu_offload bug;
            #  tracked for future resolution)
            with gr.Row(visible=False) as _i2v_row:
                ref_image_input = gr.Image(
                    label="参考图（图生视频，即将上线）",
                    type="pil",
                    sources=["upload", "clipboard"],
                    show_label=True,
                    placeholder="图生视频功能正在调试中，敬请期待",
                )
            with gr.Row():
                gr.Markdown(
                    "💡 图生视频（上传参考图作为视频起始帧）功能正在调试中，当前暂不可用。"
                )

            with gr.Row():
                size_dropdown = gr.Dropdown(
                    choices=[c[0] for c in SIZE_CHOICES],
                    value=SIZE_CHOICES[1][0],
                    label="分辨率",
                    info="512 高度档位生成最快，768 更清晰但更慢",
                )
                frames_dropdown = gr.Dropdown(
                    choices=[c[0] for c in FRAMES_CHOICES],
                    value=FRAMES_CHOICES[1][0],
                    label="视频时长",
                    info="帧数越多视频越长，耗时线性增加",
                )
                num_inference_steps = gr.Slider(
                    minimum=20, maximum=60, value=40, step=5,
                    label="推理步数",
                    info="去噪迭代次数：40 步效果与速度均衡；越多越精细但更慢",
                )

            with gr.Row():
                output_dir_input = gr.Textbox(value=self.default_output_dir, label="输出目录")

            with gr.Row():
                generate_btn = gr.Button("生成视频", variant="primary")

            with gr.Row():
                status_output = gr.Textbox(label="状态", interactive=False, lines=3)

            with gr.Row():
                video_output = gr.Video(label="生成的视频", height=360)

            generate_btn.click(
                fn=self.generate_video,
                inputs=[
                    prompt_input,
                    negative_prompt_input,
                    size_dropdown,
                    frames_dropdown,
                    num_inference_steps,
                    output_dir_input,
                    ref_image_input,
                ],
                outputs=[video_output, status_output],
            )

        return tab

    # ------------------------------------------------------------------ #
    # Handler
    # ------------------------------------------------------------------ #
    def generate_video(
        self,
        prompt: str,
        negative_prompt: str,
        size_label: str,
        frames_label: str,
        num_inference_steps: int,
        output_dir: str,
        ref_image=None,
    ) -> Tuple[str, str]:
        """Generate a video; returns (video_path_or_None, status_text)"""
        try:
            if not prompt or not prompt.strip():
                return None, "错误：请输入视频提示词"

            if not self.video_service.model_ready():
                return None, (
                    "错误：LTX-Video 模型未下载。请先运行下载脚本：\n"
                    "  .venv/Scripts/python _download_ltx.py\n"
                    "（约 14GB，走 hf-mirror）"
                )

            width = height = 512
            for label, w, h in SIZE_CHOICES:
                if label == size_label:
                    width, height = w, h
                    break
            num_frames = 97
            for label, f in FRAMES_CHOICES:
                if label == frames_label:
                    num_frames = f
                    break

            # Free VRAM used by image models before loading the video model
            if self.on_before_generate:
                self.on_before_generate()

            logger.info(
                f"Generating video | {width}x{height} | {num_frames} frames | "
                f"{num_inference_steps} steps | prompt: {prompt[:80]}"
                f" | mode={'I2V' if ref_image is not None else 'T2V'}"
            )
            meta = self.video_service.generate_video(
                prompt=prompt,
                negative_prompt=negative_prompt or "",
                height=height,
                width=width,
                num_frames=num_frames,
                num_inference_steps=int(num_inference_steps),
                init_image=ref_image,
                output_dir=output_dir,
                save=True,
            )

            mp4 = meta.get("mp4_path")
            if not mp4:
                return None, "生成失败：视频导出失败"

            mode = "图生视频" if ref_image is not None else "文生视频"
            status = (
                f"✅ {mode}完成：{meta['duration_seconds']} 秒，"
                f"{meta['width']}x{meta['height']}，{meta['num_frames']} 帧，"
                f"{num_inference_steps} 步\n保存至 {mp4}"
            )
            return mp4, status

        except Exception as e:
            logger.error(f"Error generating video: {e}", exc_info=True)
            return None, f"错误：{str(e)}"
