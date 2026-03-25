"""
Main Gradio Application for Face Generator
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
from services.scoring_service import ScoringService
from gradio_ui.generation_tab import GenerationTab

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FaceGeneratorApp:
    """Main application for face generation"""

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
        self.scoring_service = ScoringService()

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
            title="多角度人脸生成器",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as app:
            # Header
            gr.Markdown(
                """
                # 🎭 多角度人脸生成器

                基于Stable Diffusion和InsightFace的AI人脸生成工具，支持多角度生成、质量评分和智能筛选。

                ---
                """
            )

            # Create tabs
            with gr.Tabs():
                # Generation Tab
                generation_tab = GenerationTab(
                    generation_service=self.generation_service,
                    scoring_service=self.scoring_service,
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

                💡 **提示**: 先在"多角度人脸生成"标签中生成图片，然后使用质量评分功能筛选最佳结果。

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

            with gr.Column():
                gr.Markdown("### 界面配置")
                theme_dropdown = gr.Dropdown(
                    choices=["default", "soft", "glass"],
                    value="soft",
                    label="主题风格"
                )

                language_dropdown = gr.Dropdown(
                    choices=["中文", "English"],
                    value="中文",
                    label="语言 / Language"
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
               - 切换到"多角度人脸生成"标签
               - 输入生成提示词（例如："一位年轻女性的肖像，自然光照"）
               - 调整生成参数（数量、引导系数、推理步数）
               - 点击"生成图片"按钮

            2. **质量评分**
               - 确保"启用质量评分"选项已勾选
               - 设置质量阈值（0.0-1.0，默认0.7）
               - 生成后会自动显示每张图片的质量分数

            3. **保存最佳图片**
               - 生成完成后，点击"保存最佳图片"
               - 只有质量分数 >= 阈值的图片会被保存

            ### 参数说明

            - **生成数量**: 一次生成的图片数量（1-10张）
            - **引导系数**: 控制生成结果与提示词的匹配程度（7.5-15.0效果较好）
            - **推理步数**: 生成过程中的迭代步数（越多越精细但越慢）
            - **质量阈值**: 质量评分的最低要求（0.0-1.0）

            ### 技术架构

            - **生成模型**: Stable Diffusion
            - **人脸检测**: InsightFace
            - **质量评分**: 深度学习质量评估模型
            - **界面框架**: Gradio

            ### 常见问题

            **Q: 生成速度很慢怎么办？**
            A: 可以减少推理步数或生成数量。如果有GPU，确保正确安装了CUDA。

            **Q: 质量评分不准确？**
            A: 可以尝试调整质量阈值。不同风格的图片可能需要不同的阈值。

            **Q: 如何获得更好的生成效果？**
            A: 优化提示词描述，增加引导系数，或使用更多推理步数。

            ### 开发者信息

            - 版本: 0.1.0
            - 许可: MIT License
            - 源码: GitHub
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
            quiet=False
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="多角度人脸生成器")
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
