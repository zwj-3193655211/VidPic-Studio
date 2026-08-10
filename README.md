# 🎨 AI 图片生成器

基于 Stable Diffusion 的本地 AI 图片生成工具（Gradio 网页界面，纯本地推理，无需联网）。

## ✨ 特性

- **🖼️ 文生图**: 输入提示词，本地生成图片
- **⚡ 批量生成**: 一次生成多张图片（1-10 张）
- **🎛️ 参数可调**: 引导系数、推理步数自由调节
- **🖥️ 友好的图形界面**: 基于 Gradio
- **💾 智能内存管理**: 支持 attention slicing、float16 精度优化

## 🚀 快速开始

### 一键启动（Windows）

**双击 `run.bat`** 即可启动，脚本会自动：

1. 检测本地模型（魔搭缓存的 SD1.5，存在则免联网）
2. 选择正确的 Python 环境（优先 Anaconda，含 CUDA 版 torch）
3. 检查并安装缺失依赖
4. 启动应用并打开浏览器

浏览器访问: `http://127.0.0.1:7860`

### 手动启动

```bash
# 使用本地模型（魔搭下载的 SD1.5）
python app.py --model-path "C:/Users/31936/.cache/modelscope/models/AI-ModelScope--stable-diffusion-v1-5/snapshots/master"

# 使用 HuggingFace 在线模型（首次生成自动下载约 4GB）
python app.py

# 自定义输出目录 / 创建公开分享链接
python app.py --output-dir ./my_output --share
```

## 📖 使用指南

1. 在"图片生成"标签中输入提示词（例如："一位年轻女性的肖像，自然光照"）
2. 调整参数：
   - **生成数量**: 1-10 张
   - **引导系数**: 7.5-15.0（越高越符合提示词）
   - **推理步数**: 10-100（越多越精细，越慢）
3. 点击"生成图片"，等待结果展示在画廊中

## 🏗️ 项目结构

```
face-generator/
├── app.py                      # 主应用程序
├── requirements.txt            # 依赖列表
├── run.bat / run.sh            # 一键启动脚本
├── services/                   # 服务层
│   ├── generation_service.py   # 生成服务（门面）
│   └── sd_generation_service.py # Stable Diffusion服务
├── gradio_ui/                  # UI组件
│   └── generation_tab.py       # 生成标签页
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

- **生成模型**: Stable Diffusion（diffusers，本地推理）
- **界面框架**: Gradio
- **后端**: Python + PyTorch（CUDA）

## 📝 开发状态

当前版本: 0.3.0（2026-08-10 简化重构：移除质量评分/人脸检测占位模块，聚焦纯图片生成）

### 已完成功能 ✅
- ✅ 文生图（单张/批量）
- ✅ Gradio 完整界面
- ✅ GPU 加速（RTX 5060 实测 ~4 秒/张）
- ✅ 本地模型加载（魔搭缓存，免联网）
- ✅ 一键启动脚本（run.bat）
- ✅ 测试（12 passed）

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
