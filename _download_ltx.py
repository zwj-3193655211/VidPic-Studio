"""Download LTX-Video (diffusers format) via hf-mirror into models/ltx_video."""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

target = r"D:\face-generator\models\ltx_video"
os.makedirs(target, exist_ok=True)
print("downloading Lightricks/LTX-Video ->", target)
p = snapshot_download(
    repo_id="Lightricks/LTX-Video",
    local_dir=target,
    local_dir_use_symlinks=False,
)
print("DONE:", p)
