"""
JoeUploadNPZ Node - upload local .npz file from web UI to
ComfyUI output/hymotion_npz directory, then output saved path.
"""

import os
import uuid
from typing import Tuple

import folder_paths
from aiohttp import web
from server import PromptServer


def _safe_npz_name(filename: str) -> str:
    name = os.path.basename(filename or "").strip()
    if not name:
        name = f"upload_{uuid.uuid4().hex}.npz"
    if not name.lower().endswith(".npz"):
        name = f"{name}.npz"
    return name.replace("\\", "_").replace("/", "_")


@PromptServer.instance.routes.post("/hymotion/upload_npz")
async def hymotion_upload_npz(request):
    try:
        reader = await request.multipart()
        file_field = None

        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "file":
                file_field = part
                break

        if file_field is None or not file_field.filename:
            return web.json_response({"ok": False, "error": "No file provided."}, status=400)

        original_name = file_field.filename
        if not original_name.lower().endswith(".npz"):
            return web.json_response({"ok": False, "error": "Only .npz files are allowed."}, status=400)

        output_dir = folder_paths.get_output_directory()
        target_dir = os.path.join(output_dir, "hymotion_npz")
        os.makedirs(target_dir, exist_ok=True)

        safe_name = _safe_npz_name(original_name)
        final_path = os.path.join(target_dir, safe_name)
        if os.path.exists(final_path):
            stem, ext = os.path.splitext(safe_name)
            safe_name = f"{stem}_{uuid.uuid4().hex[:8]}{ext}"
            final_path = os.path.join(target_dir, safe_name)

        with open(final_path, "wb") as f:
            while True:
                chunk = await file_field.read_chunk()
                if not chunk:
                    break
                f.write(chunk)

        rel_path = f"output/hymotion_npz/{safe_name}".replace("\\", "/")
        return web.json_response({"ok": True, "npz_path": rel_path})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


class JoeUploadNPZ:
    @classmethod
    def INPUT_TYPES(cls):
        npz_files = folder_paths.get_filename_list("hymotion_npz")
        if not npz_files:
            npz_files = ["none"]
        return {
            "required": {
                "npz_name": (
                    npz_files,
                    {
                        "tooltip": "历史 NPZ 文件下拉列表（output/input 的 hymotion_npz）。",
                    },
                ),
                "npz_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "tooltip": "通过上传自动写入；若为空则使用 npz_name。格式: output/hymotion_npz/xxx.npz",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("npz_path",)
    FUNCTION = "get_npz_path"
    CATEGORY = "HY-Motion/Tools"
    OUTPUT_NODE = True

    def get_npz_path(self, npz_name: str, npz_path: str) -> Tuple[str]:
        path = (npz_path or "").strip().replace("\\", "/")

        if not path and npz_name and npz_name != "none":
            full_path = folder_paths.get_full_path("hymotion_npz", npz_name)
            if full_path and os.path.exists(full_path):
                output_dir = os.path.abspath(folder_paths.get_output_directory()).replace("\\", "/")
                input_dir = os.path.abspath(folder_paths.get_input_directory()).replace("\\", "/")
                full_norm = os.path.abspath(full_path).replace("\\", "/")

                if full_norm.startswith(output_dir + "/"):
                    rel = full_norm[len(output_dir) + 1:]
                    path = f"output/{rel}"
                elif full_norm.startswith(input_dir + "/"):
                    rel = full_norm[len(input_dir) + 1:]
                    path = f"input/{rel}"
                else:
                    path = full_norm
            else:
                path = npz_name.replace("\\", "/")

        return {"ui": {"npz_path": [path]}, "result": (path,)}


NODE_CLASS_MAPPINGS = {
    "JoeUploadNPZ": JoeUploadNPZ,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JoeUploadNPZ": "Joe Upload NPZ",
}

