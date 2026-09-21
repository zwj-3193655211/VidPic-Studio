"""
模型注册表：集中管理已知模型（路径、类型、UI 参数方案）。

新增模型只需在此加一项：
- type "diffusers"          -> 标准 diffusers 目录（SD1.5 / SDXL 等，自动识别 pipeline 类）
- type "sdxl_single_file"   -> SDXL 单文件 checkpoint + 基础组件目录（墨幽等社区模型）

所有模型文件已迁移到项目目录 models/ 下，不再依赖 ~/.cache
"""

import os

# 项目根目录（向上找一级，即项目根目录）
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_MODELS_DIR = os.path.join(_PROJECT_ROOT, "models")


def _m(p: str) -> str:
    """相对于项目 models/ 目录的路径"""
    return os.path.join(_MODELS_DIR, p)


MODELS = {
    # ---- SDXL Base（官方原版，diffusers 目录）----
    "sdxl_base": {
        "name": "SDXL Base",
        "type": "diffusers",
        "path": _m("sdxl_base"),
        "base_dir": None,
        "size_choices": [("1024x1024", 1024, 1024), ("832x1216", 832, 1216), ("1216x832", 1216, 832)],
        "size_default": "1024x1024",
        "steps_default": 25,
        "steps_range": (5, 60, 5),
        "guidance_default": 5.5,
        "guidance_range": (1.0, 15.0, 0.5),
        "num_images_default": 4,
        "negative_prompt_default": "lowres, bad anatomy, bad hands, extra fingers, blurry",
    },

    # ---- 墨幽人造人XL（SDXL 微调，单文件 ckpt，需 SDXL base 组件作骨架）----
    "moyu_xl": {
        "name": "墨幽人造人XL",
        "type": "sdxl_single_file",
        "path": _m("moyu_xl/XLMoyouArtificial_v01.safetensors"),
        "base_dir": _m("sdxl_base"),          # 复用 SDXL base 目录作骨架
        "size_choices": [("1024x1024", 1024, 1024), ("832x1216", 832, 1216), ("1216x832", 1216, 832)],
        "size_default": "1024x1024",
        "steps_default": 28,
        "steps_range": (5, 60, 5),
        "guidance_default": 5.5,
        "guidance_range": (1.0, 15.0, 0.5),
        "num_images_default": 4,
        "negative_prompt_default": "lowres, bad anatomy, bad hands, extra fingers, blurry",
    },

    # ---- RealVisXL V5（SDXL 真人微调，单文件 ckpt）----
    "realvisxl": {
        "name": "RealVisXL V5",
        "type": "sdxl_single_file",
        "path": _m("realvisxl/RealVisXL_V5.0_fp16.safetensors"),
        "base_dir": _m("sdxl_base"),          # 复用 SDXL base 目录作骨架
        "size_choices": [("1024x1024", 1024, 1024), ("832x1216", 832, 1216), ("1216x832", 1216, 832)],
        "size_default": "1024x1024",
        "steps_default": 25,
        "steps_range": (5, 60, 5),
        "guidance_default": 5.0,
        "guidance_range": (1.0, 15.0, 0.5),
        "num_images_default": 4,
        "negative_prompt_default": "lowres, bad anatomy, bad hands, extra fingers, blurry, deformed",
    },
}

DEFAULT_MODEL = "realvisxl"


def available_models() -> dict:
    """Return {key: display_name} for all registered models"""
    return {k: v["name"] for k, v in MODELS.items()}


def get_model(key: str) -> dict:
    """Get model spec by key"""
    if key not in MODELS:
        raise KeyError(f"未知模型: {key}，可用: {list(MODELS.keys())}")
    return MODELS[key]
