"""
Tests for GenerationService model switching
"""

import pytest

from services.generation_service import GenerationService


class TestModelSwitching:
    """Tests for switching between registry models"""

    def test_init_uses_registry_path_by_default(self):
        """Default model uses the registry path (now in project models/ directory)"""
        svc = GenerationService()
        assert svc.model_key == "realvisxl"
        assert "models" in svc.sd_service.model_name and "realvisxl" in svc.sd_service.model_name

    def test_init_model_path_override_applies_to_initial_model(self):
        """--model-path style override applies only to the initial model"""
        svc = GenerationService(model_path="/fake/override/path")
        assert svc.sd_service.model_name == "/fake/override/path"

    def test_switch_model_uses_registry_path_not_override(self):
        """
        Switching models must use the registry path, NOT the initial
        --model-path override (regression: switching to 墨幽 used to load
        the SD1.5 dir as the ckpt and fail with "SDXL checkpoint not found").
        """
        svc = GenerationService(model_path="/fake/override/path")
        name = svc.switch_model("moyu_xl")
        assert name == "墨幽人造人XL"
        assert "XLMoyouArtificial" in svc.sd_service.model_name
        assert svc.sd_service.model_type == "sdxl_single_file"

    def test_switch_to_unknown_model_raises(self):
        svc = GenerationService()
        with pytest.raises(KeyError):
            svc.switch_model("does-not-exist")
