# 快速恢复指南

## 🚀 30秒快速启动

```bash
# 1. 进入项目目录
cd ~/Documents/face-generator

# 2. 运行测试（验证环境）
python -m pytest tests/ -v

# 3. 启动应用（双击 run.bat 也行）
python app.py --model-path "C:/Users/31936/.cache/modelscope/models/AI-ModelScope--stable-diffusion-v1-5/snapshots/master"
```

**浏览器访问**: http://127.0.0.1:7860

> **一键启动**: 双击 `run.bat` 会自动检测本地模型（魔搭缓存目录存在即用本地模型，无需联网）并启动。

## ⚡ 当前环境配置（2026-08-10）

| 项 | 状态 |
|---|---|
| torch | **2.11.0+cu128**（CUDA 版，全局环境） |
| GPU | RTX 5060 Laptop 8GB，生成一张 512x512 约 **4 秒**（20 步） |
| SD 模型 | 魔搭本地缓存 `~/.cache/modelscope/models/AI-ModelScope--stable-diffusion-v1-5/snapshots/master`（4GB，**无需联网**） |
| HuggingFace | 直连被墙，代理（127.0.0.1:33210）对 HF 不稳定；如需在线下载模型，优先走代理或 hf-mirror |

**模型说明**：runwayml/stable-diffusion-v1-5（diffusers 格式，safetensors 权重）。本地模型来自魔搭 AI-ModelScope 镜像，与 HF 原版等价。

---

## 📊 当前状态

**版本**: v0.2.0
**进度**: 6/8 任务完成 (75%)
**测试**: 13 passed, 9 skipped

### 已完成 ✅
- ✅ Stable Diffusion 完整集成
- ✅ 多角度生成系统（8种角度）
- ✅ Gradio 完整UI
- ✅ 测试框架（13个通过）
- ✅ 依赖安装完成

### 待开发 ⏳
- ⏳ Task #4: 训练流程集成
- ⏳ Task #5: 最终测试

---

## 📁 核心文件

| 文件 | 功能 | 重要性 |
|------|------|--------|
| `services/sd_generation_service.py` | SD生成服务 | ⭐⭐⭐ |
| `app.py` | 主应用 | ⭐⭐⭐ |
| `gradio_ui/generation_tab.py` | 生成UI | ⭐⭐ |
| `demo_sd_generation.py` | 演示脚本 | ⭐ |

---

## 💡 下次做什么？

### 选项A: 测试实际生成（推荐）
```bash
python demo_sd_generation.py
# 会下载~5GB模型，首次较慢
```

### 选项B: 继续开发
开始 **Task #4: 集成训练流程**
- 实现训练UI
- 集成LoRA微调
- 添加模型管理

### 选项C: 完善功能
- 集成InsightFace人脸检测
- 实现真实质量评分
- 优化性能

---

## 🔧 常用命令

```bash
# 测试
pytest tests/ -v                    # 所有测试
pytest tests/test_sd_generation.py  # SD测试

# 运行
python app.py                       # 启动应用
python demo_sd_generation.py        # 演示脚本

# Git
git status                          # 查看状态
git log --oneline -5                # 最近提交
git diff                            # 查看改动
```

---

## 📖 详细文档

- **完整进度**: 查看 `PROGRESS.md`
- **用户文档**: 查看 `README.md`
- **代码注释**: 查看各文件内的docstring

---

**最后更新**: 2026-03-25
**准备好继续开发了！** 🚀
