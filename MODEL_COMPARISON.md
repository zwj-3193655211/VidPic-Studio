# 开源图片生成模型调研 & 部署对比

> 2026-08-10 · 面向本机（RTX 5060 Laptop 8GB / 32GB RAM / ~66GB 可用磁盘 / torch 2.11+cu128 / diffusers 0.37 / 全局 Anaconda）
> 本机网络现实：HuggingFace 直连被墙，代理 127.0.0.1:33210 对 HF 不稳定；**ModelScope（魔搭）直连畅通**（~20MB/s）

## 总览表

| 模型 | 阵营 | 参数量 | 可用权重(fp16) | 磁盘占用 | 8GB显存 | 生成速度(RTX5060) | 中文提示词 | 真人脸 | 获取 | 集成难度 |
|---|---|---|---|---|---|---|---|---|---|---|
| **SD1.5**（当前） | 国际 | 0.86B | ~4GB | 4GB | ✅ 流畅 | **~4秒/张** (20步) | 一般 | 一般 | 魔搭✅已装 | 已完成 |
| **SDXL base** | 国际 | 3.5B | ~7GB | 7GB | ⚠️ 紧(切片+tiling) | 15~30秒 (25步) | 好 | 好 | 魔搭✅ | 低(改pipeline类) |
| **SDXL-Lightning** | 国际 | 3.5B | ~7GB | 7GB+ | ⚠️ 同上 | **3~6秒** (4步) | 好 | 好 | 魔搭✅(需过滤) | 低 |
| **RealVisXL V5** | 国际微调 | 3.5B | ~7GB | 7GB | ⚠️ 同上 | 15~30秒 | 好 | **极好**(皮肤/五官) | HF(代理) | 低 |
| **墨幽人造人** | 国内微调 | 3.5B | ~7GB | 7GB | ⚠️ 同上 | 15~30秒 | 极好 | **极好**(国内最火真人) | HF(代理) | 低 |
| **ChilloutMix / majicMIX / GhostMix** | 国内微调 | 0.86B | ~4GB | 4GB | ✅ 流畅 | ~4秒 | 好 | 好(写真风) | HF(代理) | 低 |
| **Kolors 可图** | 国内(快手) | 2.6B+6B编码器 | ~11.5GB | 11.5GB | ❌→⚠️ 需CPU offload | 20~40秒 | **极强** | 好 | 魔搭✅ | **高**(ChatGLM编码器+transformers5兼容风险) |
| **万相 Wanx2.1** | 国内(阿里) | ~1.3B DiT | ~3GB | 3GB | ✅ | 10~20秒 | 强 | 中 | 魔搭ID未确认 | 中(专用pipeline) |
| **混元 HunyuanDiT** | 国内(腾讯) | 1.5B+LLaMA7B | ~14GB | 14GB | ❌ LLaMA编码器爆显存 | — | 强 | 中 | 需确认 | 高 |
| **SD3.5 Medium** | 国际 | 2.5B+T5-XXL | ~15GB | 15GB | ❌ T5-XXL 9.8GB>8GB | — | 中 | 好 | 魔搭✅ | 中(许可证限制) |
| **FLUX.1-schnell** | 国际 | 12B | GGUF Q4~7GB | 7GB | ⚠️ 量化+offload | 1~3分钟 | 一般 | 极好 | HF(代理) | **高**(GGUF工具链) |
| **Seedream 3.0** | 国内(字节) | 闭源 | — | — | — | — | 强 | **极好** | API only | ❌ 不适用 |

## 部署可行性结论（按 8GB 显存排）

### ✅ 直接可玩（魔搭直连，当天搞定）
1. **SD1.5** —— 已跑通，4秒/张（当前基准）
2. **SDXL base** —— 升级性价比最高的一步：原生 1024 分辨率，画质明显提升。下载过滤后 ~7GB，显存用 attention slicing + VAE tiling 压住
3. **SDXL-Lightning** —— 同上大小，4 步出图，适合快速出图对比

### ⚠️ 能玩但需折腾
4. **RealVisXL / 墨幽** —— 真人脸天花板，但需要 HF 下载（VPN 通时），集成和 SDXL 一样
5. **Kolors** —— 中文提示词最强国产模型，但：权重 11.5GB 超显存需 CPU offload；文本编码器是 ChatGLM3（当前 transformers 5.x 可能不兼容，需验证/降级）；魔搭直连可下
6. **FLUX.1-schnell** —— 开源最强画质，12B 参数，必须 GGUF 量化（~7GB）+ 专用加载工具，单张 1-3 分钟

### ❌ 本机不推荐
7. **混元 DiT** —— LLaMA-7B 文本编码器 ~13GB，8GB 显存无解
8. **SD3.5 Medium** —— T5-XXL 编码器 fp16 就 9.8GB，超显存；且许可证含使用条款限制
9. **Seedream** —— 闭源，只有 API，不属于"本地开源模型"

## 推荐试玩路线

```
第1步  SD1.5（已有）        ← 基准，先感受 512 分辨率
第2步  SDXL base            ← 画质大跳变，1024 原生分辨率
第3步  SDXL-Lightning       ← 体验 4 步出图的快感
第4步  RealVisXL / 墨幽     ← 真人脸天花板（等 VPN 通下 HF）
第5步  Kolors               ← 中文提示词体验（挑战项）
第6步  FLUX GGUF            ← 终极挑战（折腾项，可选）
```

## 各模型下载命令（魔搭，过滤无用文件）

```bash
# SDXL base（只需 fp16 子集 ~7GB）
python -c "
from modelscope import snapshot_download
snapshot_download('AI-ModelScope/stable-diffusion-xl-base-1.0',
    allow_patterns=['unet/diffusion_pytorch_model.fp16.safetensors',
                    'text_encoder*/**', 'vae/**', 'tokenizer*/**',
                    'scheduler/**', 'feature_extractor/**', 'model_index.json',
                    '*.json', '*.txt'])"

# SDXL-Lightning（4步版本，过滤掉多余ckpt）
python -c "
from modelscope import snapshot_download
snapshot_download('AI-ModelScope/SDXL-Lightning',
    allow_patterns=['sdxl_lightning_4step*.safetensors',
                    'unet/**', 'text_encoder*/**', 'vae/**', 'tokenizer*/**',
                    'scheduler/**', 'model_index.json', '*.json', '*.txt'])"

# Kolors（unet fp16 + 编码器，注意 transformers 兼容性）
python -c "
from modelscope import snapshot_download
snapshot_download('AI-ModelScope/Kolors',
    allow_patterns=['unet/diffusion_pytorch_model.fp16.safetensors',
                    'text_encoder/**', 'vae/**', 'tokenizer*/**',
                    'scheduler/**', 'model_index.json', '*.json', '*.txt'])"
```

## 代码改造需求

| 模型 | 需要改什么 |
|---|---|
| SD1.5 / SDXL / Lightning / RealVis / 墨幽 / ChilloutMix 等 SD 系 | `load_model` 读 `model_index.json` 自动选 pipeline 类（SD1.5→`StableDiffusionPipeline`，SDXL→`StableDiffusionXLPipeline`），SDXL 默认 1024 分辨率 + `enable_vae_tiling` |
| Kolors | `KolorsPipeline`（diffusers 0.30+ 已支持）+ 验证 transformers 5.x 下 ChatGLM 编码器可用性（可能需 `pip install "transformers<5"`） |
| FLUX GGUF | 单独工具链（gguf 量化权重 + diffusers GGUF 加载或 llama.cpp），需另建入口 |

## 磁盘预算（66GB 可用）

| 方案 | 占用 |
|---|---|
| SD1.5 + SDXL base（推荐起步） | ~11GB |
| + SDXL-Lightning | ~18GB |
| + Kolors | ~30GB |
| + FLUX GGUF | ~37GB |
| 全家桶（含 HF 微调） | ~50GB ✅ 都放得下 |
