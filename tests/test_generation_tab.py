"""
Tests for GenerationTab
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from gradio_ui.generation_tab import GenerationTab
except ImportError:
    pytest.skip("Gradio or dependencies not available", allow_module_level=True)

from services.generation_service import GenerationService


@pytest.fixture
def mock_generation_service():
    """Mock generation service"""
    service = MagicMock(spec=GenerationService)
    service.model_key = "realvisxl"
    return service


@pytest.fixture
def generation_tab(mock_generation_service, tmp_path):
    """Create generation tab instance"""
    return GenerationTab(
        generation_service=mock_generation_service,
        default_output_dir=str(tmp_path)
    )


class TestGenerationTabInit:
    """Tests for GenerationTab initialization"""

    def test_initialization(self, mock_generation_service, tmp_path):
        """Test that GenerationTab initializes correctly"""
        tab = GenerationTab(
            generation_service=mock_generation_service,
            default_output_dir=str(tmp_path)
        )

        assert tab.generation_service == mock_generation_service
        assert tab.default_output_dir == tmp_path

    def test_output_dir_creation(self, mock_generation_service, tmp_path):
        """Test that output directory is created if it doesn't exist"""
        output_dir = tmp_path / "new_output"
        assert not output_dir.exists()

        GenerationTab(
            generation_service=mock_generation_service,
            default_output_dir=str(output_dir)
        )

        assert output_dir.exists()


class TestGenerationTabBuild:
    """Tests for build method"""

    def test_build_creates_tab(self, generation_tab):
        """Test that build creates a Gradio tab"""
        with patch('gradio_ui.generation_tab.gr') as mock_gr:
            mock_tab = MagicMock()
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_tab)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_gr.Tab.return_value = mock_context

            result = generation_tab.build()

            assert result == mock_tab


class TestGenerateImages:
    """Tests for generate_images method"""

    def test_generate_images_empty_prompt(self, generation_tab):
        """Test that empty prompt returns error"""
        gallery, status = generation_tab.generate_images(
            model_key="realvisxl",
            prompt="",
            negative_prompt="",
            num_images=4,
            guidance_scale=7.5,
            num_inference_steps=30,
            size_label="512x512",
            output_dir=str(generation_tab.default_output_dir)
        )

        assert gallery == []
        assert "错误：请输入生成提示词" in status

    @pytest.mark.skipif(True, reason="Need mock PIL Images for full testing")
    def test_generate_images_success(self, generation_tab, mock_generation_service):
        """Test successful image generation"""
        # This would need PIL Image mocks to work properly
        pass
