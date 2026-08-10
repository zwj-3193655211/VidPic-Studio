# 🎬 VidPic Studio · AI 图影工坊

基于 Stable Diffusion / LTX-Video 的本地 AI 图文视频生成工具（Gradio 网页界面，纯本地推理，无需联网）。

## ✨ 特性

- **🖼️ 文生图**: 输入提示词，本地生成图片（SD1.5 / SDXL / 墨幽 / RealVisXL）
- **🖼️ 图生图**: 上传参考图按构图/风格生成
- **🎬 视频生成**: 输入提示词，本地生成短视频（LTX-Video 2B）
- **⚡ 批量生成**: 一次生成多张图片（1-10 张）
- **🎛️ 参数可调**: 引导系数、推理步数、参考强度自由调节
- **🖥️ 友好的图形界面**: 基于 Gradio
- **💾 智能内存管理**: 支持 CPU offload、float16 精度优化（8GB 显存可跑）

## 🚀 快速开始

### 一键启动（Windows）

**双击 `run.bat`** 即可启动，脚本会自动：

1. 检测本地模型（`models/` 目录：4 个生图模型 + LTX 视频模型）
2. 选择正确的 Python 环境（优先 `.venv`）
3. 检查并安装缺失依赖
4. 启动应用并打开浏览器

浏览器访问: `http://127.0.0.1:7860`

### 手动启动

```bash
# 使用本地模型（models/ 目录由 models_registry.py 自动管理）
python app.py

# 自定义输出目录 / 创建公开分享链接
python app.py --output-dir ./my_output --share
```

## 📖 使用指南

### 图片生成
1. 在"图片生成"标签中输入提示词（建议英文，效果最佳，例如：`a young woman portrait, soft natural light`）
2. 调整参数：
   - **生成数量**: 1-10 张
   - **引导系数**: 5-8（越高越符合提示词，过高会过曝）
   - **推理步数**: 25-30（越多越精细，越慢）
3. 可选：上传参考图切换图生图模式，用"参考强度"控制保留程度
4. 点击"生成图片"，等待结果展示在画廊中

### 视频生成
1. 在"视频生成"标签中输入提示词
2. 选择分辨率、帧数、步数
3. 点击"生成视频"，等待 MP4 输出（8GB 显卡约需数分钟）

## 🏗️ 项目结构

```
vidpic-studio/
├── app.py                      # 主应用程序
├── requirements.txt            # 依赖列表
├── run.bat / run.sh            # 一键启动脚本
├── services/                   # 服务层
│   ├── generation_service.py   # 图片生成服务（门面）
│   ├── sd_generation_service.py # Stable Diffusion服务
│   └── ltx_video_service.py    # LTX 视频生成服务
├── gradio_ui/                  # UI组件
│   ├── generation_tab.py       # 图片生成标签页
│   └── video_generation_tab.py # 视频生成标签页
└── tests/                      # 测试文件
    ├── test_app.py
    ├── test_generation_tab.py
    └── test_sd_generation.py
```

## 🧪 运行测试

```bash
pytest tests/ -v
```

## 🔧 技术栈

- **生图模型**: Stable Diffusion（diffusers，本地推理）
- **视频模型**: LTX-Video 2B（diffusers，本地推理）
- **界面框架**: Gradio
- **后端**: Python + PyTorch（CUDA）

## 📝 开发状态

当前版本: 0.4.0（2026-08-10：更名 VidPic Studio，加入 LTX-Video 视频生成）

### 已完成功能 ✅
- ✅ 文生图（单张/批量，4 个模型）
- ✅ 图生图（参考图 + 强度控制）
- ✅ 视频生成（LTX-Video 2B）
- ✅ Gradio 完整界面（参数说明内联提示）
- ✅ GPU 加速 + CPU offload（RTX 5060 8GB 实测）
- ✅ 一键启动脚本（run.bat）

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
