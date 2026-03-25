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
from services.scoring_service import ScoringService


@pytest.fixture
def mock_generation_service():
    """Mock generation service"""
    service = MagicMock(spec=GenerationService)
    return service


@pytest.fixture
def mock_scoring_service():
    """Mock scoring service"""
    service = MagicMock(spec=ScoringService)
    return service


@pytest.fixture
def generation_tab(mock_generation_service, mock_scoring_service, tmp_path):
    """Create generation tab instance"""
    return GenerationTab(
        generation_service=mock_generation_service,
        scoring_service=mock_scoring_service,
        default_output_dir=str(tmp_path)
    )


class TestGenerationTabInit:
    """Tests for GenerationTab initialization"""

    def test_initialization(self, mock_generation_service, mock_scoring_service, tmp_path):
        """Test that GenerationTab initializes correctly"""
        tab = GenerationTab(
            generation_service=mock_generation_service,
            scoring_service=mock_scoring_service,
            default_output_dir=str(tmp_path)
        )

        assert tab.generation_service == mock_generation_service
        assert tab.scoring_service == mock_scoring_service
        assert tab.default_output_dir == tmp_path
        assert tab.current_batch_dir is None

    def test_output_dir_creation(self, mock_generation_service, mock_scoring_service, tmp_path):
        """Test that output directory is created if it doesn't exist"""
        output_dir = tmp_path / "new_output"
        assert not output_dir.exists()

        GenerationTab(
            generation_service=mock_generation_service,
            scoring_service=mock_scoring_service,
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

            assert generation_tab.build() == mock_tab


class TestGenerateFaces:
    """Tests for generate_faces method"""

    def test_generate_faces_empty_prompt(self, generation_tab):
        """Test that empty prompt returns error"""
        gallery, status, metrics = generation_tab.generate_faces(
            prompt="",
            num_images=4,
            guidance_scale=7.5,
            num_inference_steps=50,
            enable_scoring=True,
            quality_threshold=0.7,
            output_dir=str(generation_tab.default_output_dir)
        )

        assert gallery == []
        assert "错误：请输入生成提示词" in status
        assert metrics == {}

    @pytest.mark.skipif(True, reason="Need mock PIL Images for full testing")
    def test_generate_faces_success(self, generation_tab, mock_generation_service, mock_scoring_service):
        """Test successful face generation"""
        # This would need PIL Image mocks to work properly
        pass


class TestSaveBestFaces:
    """Tests for save_best_faces method"""

    def test_save_best_faces_no_batch(self, generation_tab):
        """Test saving when no batch exists returns error"""
        status = generation_tab.save_best_faces(
            quality_threshold=0.7,
            output_dir=str(generation_tab.default_output_dir)
        )

        assert "错误：没有可保存的图片批次" in status
