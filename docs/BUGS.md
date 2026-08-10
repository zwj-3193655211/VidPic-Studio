# VidPic Studio Bug 报告

> 环境：RTX 5060 Laptop 8GB 显存 / 32GB RAM / Ryzen 9 8945HX
> 技术栈：gradio 6.17.3 / diffusers 0.39.0 / transformers 4.57.6 / torch 2.11 cu128

---

## Bug #1（严重）：T2V 视频生成高帧数/高分辨率 OOM

**现象**：文生视频（LTX-Video 2B）在 121 帧、512×768 或更高分辨率下，跑到中途 CUDA OOM，生成失败。

**复现步骤**：
1. 启动 `run.bat` → 🎬 视频生成
2. 输入提示词，分辨率 512×768，帧数 121（约 5 秒），步数 40
3. 点击生成，跑到 ~78%（31/40 步）时抛 `CUDA error: out of memory`

**日志**：
```
78%|███████████████████████████████████████████▌  | 31/40
CUDA error: out of memory
cublasLtMatmul 内部错误 → gemm_and_bias error: CUBLAS_STATUS_INTERNAL_ERROR
```

**已做的缓解**：
- `services/ltx_video_service.py` 已加 `enable_vae_tiling()` + `enable_vae_slicing()`
- UI 已标注 121 帧有 OOM 风险
- 但根本原因未解决：LTX transformer 的 attention 层中间激活值太大（121 帧 latent 很大），8GB 显存峰值不够

**建议修复方向**：
1. 启用 `enable_attention_slicing()`（需要验证 diffusers 0.39 LTXPipeline 是否支持）
2. 或升级 diffusers 到 >=0.40（可能对 LTX transformer offload 有改进）
3. 或在生成时加 `enable_sequential_cpu_offload()` 替代当前的 `enable_model_cpu_offload()`（更激进省显存但更慢）
4. 短期：UI 默认帧数已设为 97，121 仅作为可选+警告

---

## Bug #2（阻塞）：LTX 图生视频（I2V）无法在 offload 模式下工作

**现象**：`LTXImageToVideoPipeline.from_pipe(T2V_pipeline)` 后在 `cpu_offload` 状态下调用 `.generate()` 会无限卡在第一步推理，不抛异常、不报错、GPU 0% 利用率。

**复现步骤**（已反复验证 4 次）：
```python
from diffusers import LTXImageToVideoPipeline
svc = LTXVideoService()
svc.load_model()  # T2V pipeline with enable_model_cpu_offload()
pipe = LTXImageToVideoPipeline.from_pipe(svc.pipeline)
result = pipe(prompt="test", height=256, width=256, num_frames=9, num_inference_steps=5)
# ↑ 卡在 0/5，永不推进
```

**已排除的原因**：
- ❌ 不是 from_pipe 没有同步 `_all_hooks`（手动 `pipe._all_hooks = svc.pipeline._all_hooks` 无效）
- ❌ 不是 offload hook 重复注册（去掉重复 offload 调用也无效）
- ❌ 不是 image encoding 问题（**不传 image 的纯 T2V 也卡**）

**根因推测**：diffusers 0.39 的 LTXImageToVideoPipeline 在 cpu_offload (AlignDevicesHook) 状态下的 forward 路径和 T2V 管道有差异，导致某个组件 forward 时 hook 未正确触发设备切换。这是 diffusers 的内部 bug。

**当前处理**：UI 已隐藏图生视频入口并标记"即将上线"，生成过程强制走 T2V。

**建议修复方向**：
1. 升级 diffusers 到最新版（>=0.40.0），验证 I2V + offload 是否修复
2. 或改用 ComfyUI 实现 I2V（ComfyUI 的 offload 机制独立于 diffusers，社区已验证可行）
3. 后续 RTX 5060 8GB 的最佳视频生成体验推荐走 ComfyUI + Wan2.2-5B GGUF 或 LTX-Video GGUF 路线

---

## Bug #3（中等）：T5Tokenizer 惰性导入导致模型加载失败

**现象**：transformers 4.57+ 的 lazy module loading 使 `transformers.T5Tokenizer` 成为占位符，diffusers 的 `from_pretrained` 无法识别。

**已修复**：
- `services/ltx_video_service.py` → load_model 中 monkey-patch：
  ```python
  import transformers
  from transformers.models.t5.tokenization_t5 import T5Tokenizer as _Real
  setattr(transformers, "T5Tokenizer", _Real)
  ```

**遗留风险**：升级 transformers 到 5.x 时可能失效或产生新冲突。

---

## 已知限制（非 bug，记录用）

1. **8GB 显存上限**：T2V 推荐 ≤97 帧、≤512 分辨率；图片生图和视频生成不能同时驻留（已通过 mutex 互斥卸载解决）
2. **I2V 暂不可用**：代码已写完但因 diffusers bug 无法工作，隐藏入口
3. **LTX 模型下载**：约 27GB（T5 fp32 占 18GB + transformer fp16 4.2GB + VAE），下载需要约 30-60 分钟（hf-mirror）
4. **pip 镜像问题**：清华 pypi 源 403，需要 `-i https://pypi.org/simple` 且去掉 HTTP_PROXY 环境变量

---

## 相关文件

| 文件 | 涉及 bug |
|---|---|
| `services/ltx_video_service.py` | #1 #2 #3 |
| `gradio_ui/video_generation_tab.py` | #1 #2 |
| `app.py` | 显存互斥逻辑 |
| `models/ltx_video/` | 模型权重（约 27GB） |
