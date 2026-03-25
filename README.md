# 🎭 多角度人脸生成器 (Multi-Angle Face Generator)

基于Stable Diffusion和InsightFace的AI人脸生成工具，支持多角度生成、质量评分和智能筛选。

## ✨ 特性

- **🎨 多角度人脸生成**: 基于Stable Diffusion的高质量人脸生成
- **📊 智能质量评分**: 使用深度学习模型自动评估图片质量
- **🔍 人脸检测**: 基于InsightFace的高精度人脸检测
- **⚡ 批量处理**: 支持一次生成多张图片并进行质量筛选
- **🖥️ 友好的图形界面**: 基于Gradio的直观用户界面

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
# 基础运行
python app.py

# 使用自定义模型
python app.py --model-path /path/to/model

# 指定输出目录
python app.py --output-dir ./my_output

# 创建公开分享链接
python app.py --share
```

应用将在浏览器中打开: `http://127.0.0.1:7860`

## 📖 使用指南

### 1. 生成图片

1. 在"多角度人脸生成"标签页中输入生成提示词
2. 调整生成参数：
   - **生成数量**: 1-10张
   - **引导系数**: 7.5-15.0（越高越符合提示词）
   - **推理步数**: 10-100（越多越精细）
3. 点击"生成图片"按钮

### 2. 质量评分

- 确保"启用质量评分"选项已勾选
- 设置质量阈值（0.0-1.0，推荐0.7）
- 生成后会自动显示每张图片的质量分数

### 3. 保存最佳图片

- 生成完成后，点击"保存最佳图片"
- 只有质量分数 >= 阈值的图片会被保存

## 🏗️ 项目结构

```
face-generator/
├── app.py                      # 主应用程序
├── requirements.txt            # 依赖列表
├── README.md                   # 项目文档
├── services/                   # 服务层
│   ├── generation_service.py   # 生成服务
│   └── scoring_service.py      # 评分服务
├── gradio_ui/                  # UI组件
│   └── generation_tab.py       # 生成标签页
└── tests/                      # 测试文件
    ├── test_app.py
    └── test_generation_tab.py
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_generation_tab.py -v

# 运行带覆盖率的测试
pytest --cov=. tests/
```

## 🔧 技术栈

- **生成模型**: Stable Diffusion
- **人脸检测**: InsightFace
- **质量评估**: 深度学习质量评估模型
- **界面框架**: Gradio
- **后端**: Python + PyTorch

## 📝 开发状态

当前版本: 0.1.0

已完成功能:
- ✅ 基础项目结构
- ✅ GenerationService服务层
- ✅ ScoringService服务层
- ✅ Gradio界面组件
- ✅ 测试框架
- ✅ 主应用集成

待开发功能:
- ⏳ 实际Stable Diffusion模型集成
- ⏳ InsightFace人脸检测
- ⏳ 训练流程集成
- ⏳ 高级功能开发

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📧 联系方式

遇到问题请提交Issue或查看帮助文档。

---

**注意**: 本项目仍在开发中，部分功能为占位实现。实际使用需要下载相应的模型文件。
