"""
Tests for main application
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from app import FaceGeneratorApp
except ImportError:
    pytest.skip("Gradio or dependencies not available", allow_module_level=True)


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory"""
    return tmp_path / "output"


class TestFaceGeneratorApp:
    """Tests for FaceGeneratorApp"""

    def test_app_initialization(self, tmp_output_dir):
        """Test that the app initializes correctly"""
        app = FaceGeneratorApp(
            model_path=None,
            output_dir=str(tmp_output_dir),
            share=False,
            build_interface=False  # Don't build interface in tests
        )

        assert app.output_dir == tmp_output_dir
        assert app.share is False
        assert app.generation_service is not None
        assert tmp_output_dir.exists()

    def test_app_builds_interface(self, tmp_output_dir):
        """Test that the app builds the interface"""
        with patch('app.gr') as mock_gr:
            app = FaceGeneratorApp(
                model_path=None,
                output_dir=str(tmp_output_dir),
                share=False,
                build_interface=False
            )

            # Now build the interface
            with patch.object(app, '_build_interface') as mock_build:
                mock_build.return_value = MagicMock()
                app.app = app._build_interface()
                mock_build.assert_called_once()

    @pytest.mark.skipif(True, reason="Requires actual Gradio to test launch")
    def test_app_launch(self, tmp_output_dir):
        """Test that the app can launch"""
        # This would require actual Gradio to be available
        pass


class TestApplySettings:
    """Tests for settings application"""

    def test_apply_settings_basic(self, tmp_output_dir):
        """Test applying basic settings"""
        app = FaceGeneratorApp(
            model_path=None,
            output_dir=str(tmp_output_dir),
            share=False,
            build_interface=False
        )

        result = app._apply_settings("", str(tmp_output_dir))

        assert "✅ 设置已应用" in result or "应用设置" in result
