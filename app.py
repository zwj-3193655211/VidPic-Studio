"""
Main Gradio Application for AI Image Generator
"""

import logging
from pathlib import Path
import argparse

try:
    import gradio as gr
except ImportError:
    gr = None
    print("Gradio is not installed. Install with: pip install gradio")
    exit(1)

from services.generation_service import GenerationService
from gradio_ui.generation_tab import GenerationTab

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class _ServerNoiseFilter(logging.Filter):
    """Suppress known-harmless uvicorn/asyncio noise on Windows:

    - "Invalid HTTP request received": uvicorn warning when a client (browser
      extension, port scanner, aborted page load) sends a malformed request.
    - "Exception in callback ... ConnectionResetError [WinError 10054]":
      asyncio Proactor callback noise when a client drops the connection
      (known benign behaviour on Windows).

    Neither affects generation; they only pollute the console log.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "Invalid HTTP request received" in msg:
            return False
        # asyncio Proactor "Exception in callback ... _call_connection_lost"
        # noise on Windows. The actual WinError lives in record.exc_info, NOT in
        # getMessage() (which only holds the first log line), so we must inspect
        # the exception object itself. WinError 10054 -> ConnectionResetError,
        # 10053 -> ConnectionAbortedError (both subclasses of ConnectionError).
        if "Exception in callback" in msg and record.exc_info:
            exc = record.exc_info[1]
            if isinstance(exc, ConnectionError):
                return False
        return True


for _noise_logger_name in ("uvicorn.error", "uvicorn.access", "asyncio"):
    logging.getLogger(_noise_logger_name).addFilter(_ServerNoiseFilter())


class FaceGeneratorApp:
    """Main application for image generation"""

    def __init__(
        self,
        model_path: str = None,
        output_dir: str = "output",
        share: bool = False,
        build_interface: bool = True
    ):
        """
        Initialize the application

        Args:
            model_path: Path to the generation model
            output_dir: Default output directory
            share: Whether to create a public link
            build_interface: Whether to build the interface during init
        """
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.share = share

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize services
        logger.info("Initializing services...")
        self.generation_service = GenerationService(model_path=model_path)

        # Build UI
        self.app = None
        if build_interface:
            self.app = self._build_interface()

    def _build_interface(self) -> gr.Blocks:
        """
        Build the Gradio interface

        Returns:
            Gradio Blocks app
        """
        logger.info("Building Gradio interface...")

        with gr.Blocks(
            title="VidPic Studio - AI 图影工坊"
        ) as app:
            # Header
            gr.Markdown(
                """
                # 🎬 VidPic Studio · AI 图影工坊

                基于 Stable Diffusion 的本地图片生成工具，输入提示词即可生成图片。

                ---
                """
            )

            # Create tabs
            with gr.Tabs():
                # Generation Tab
                generation_tab = GenerationTab(
                    generation_service=self.generation_service,
                    default_output_dir=str(self.output_dir)
                )
                generation_tab.build()

                # Settings Tab
                with gr.Tab("⚙️ 设置"):
                    self._build_settings_tab()

                # Help Tab
                with gr.Tab("❓ 帮助"):
                    self._build_help_tab()

            # Footer
            gr.Markdown(
                """
                ---

                📧 **技术支持**: 遇到问题请查看帮助文档或提交Issue
                """
            )

        return app

    def _build_settings_tab(self):
        """Build the settings tab"""
        gr.Markdown("## 应用设置")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 模型配置")
                model_path_input = gr.Textbox(
                    label="模型路径",
                    placeholder="留空使用默认模型",
                    value=self.model_path or ""
                )

                output_dir_input = gr.Textbox(
                    label="输出目录",
                    value=str(self.output_dir),
                    interactive=True
                )

        with gr.Row():
            apply_settings_btn = gr.Button("应用设置", variant="primary")
            reset_settings_btn = gr.Button("重置为默认")

        with gr.Row():
            settings_status = gr.Textbox(
                label="状态",
                interactive=False
            )

        # Wire up events
        apply_settings_btn.click(
            fn=self._apply_settings,
            inputs=[model_path_input, output_dir_input],
            outputs=[settings_status]
        )

    def _build_help_tab(self):
        """Build the help tab"""
        gr.Markdown(
            """
            ## 📖 使用指南

            ### 快速开始

            1. **生成图片**
               - 切换到"图片生成"标签
               - 输入生成提示词（建议英文，效果最佳，例如：`a young woman portrait, soft natural light`）
               - 调整生成参数（数量、引导系数、推理步数）
               - 点击"生成图片"按钮

            ### 参数说明

            - **生成数量**: 一次生成的图片数量（1-10张）
            - **引导系数**: 控制生成结果与提示词的匹配程度（7.5-15.0效果较好）
            - **推理步数**: 生成过程中的迭代步数（越多越精细但越慢）

            ### 技术架构

            - **生成模型**: Stable Diffusion（本地推理，无需联网）
            - **界面框架**: Gradio

            ### 常见问题

            **Q: 生成速度很慢怎么办？**
            A: 可以减少推理步数或生成数量。如果有GPU，确保正确安装了CUDA。

            **Q: 如何获得更好的生成效果？**
            A: 优化提示词描述，增加引导系数，或使用更多推理步数。

            ### 开发者信息

            - 版本: 0.3.0
            - 许可: MIT License
            """
        )

    def _apply_settings(self, model_path: str, output_dir: str) -> str:
        """Apply settings"""
        try:
            if model_path:
                self.model_path = model_path
                # TODO: Reload model with new path

            if output_dir:
                self.output_dir = Path(output_dir)
                self.output_dir.mkdir(parents=True, exist_ok=True)

            return "✅ 设置已应用"
        except Exception as e:
            return f"❌ 应用设置失败: {str(e)}"

    def _get_custom_css(self) -> str:
        """Get custom CSS for the interface"""
        return """
        .gradio-container {
            max-width: 1200px !important;
        }

        /* Custom styling for generated images */
        .gallery-item {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }

        /* Status message styling */
        .status-success {
            color: #4caf50;
            font-weight: bold;
        }

        .status-error {
            color: f44336;
            font-weight: bold;
        }

        /* Custom button styling */
        .primary-btn {
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        }
        """

    def launch(self):
        """Launch the Gradio application"""
        logger.info("Launching application...")
        logger.info(f"Output directory: {self.output_dir}")

        self.app.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=self.share,
            show_error=True,
            quiet=False,
            theme=gr.themes.Soft(),
            css=self._get_custom_css(),
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="VidPic Studio - AI 图影工坊")
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Path to the generation model"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Default output directory"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public link"
    )

    args = parser.parse_args()

    # Create and launch app
    app = FaceGeneratorApp(
        model_path=args.model_path,
        output_dir=args.output_dir,
        share=args.share
    )
    app.launch()


if __name__ == "__main__":
    main()
