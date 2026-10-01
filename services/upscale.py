import os
import cv2
import numpy as np
import torch
from PIL import Image, ImageEnhance

EXPORT_DIR = os.getenv("EXPORT_DIR", "/tmp/realphoto_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def _find_weight():
    candidates = [
        os.getenv("REALESRGAN_MODEL", ""),
        "/app/models/RealESRGAN_x4plus.pth",
        "/workspace/models/RealESRGAN_x4plus.pth",
        "/content/realphoto_models/RealESRGAN_x4plus.pth",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None

def _resize_2k(image):
    image = image.convert("RGB")
    w, h = image.size
    scale = 2048 / max(w, h)
    out = image.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    return ImageEnhance.Sharpness(out).enhance(1.12)

def upscale_2k(image):
    """
    Использует Real-ESRGAN, если зависимости и вес доступны.
    Иначе безопасно делает качественный 2K fallback.
    """
    try:
        from spandrel import ModelLoader, ImageModelDescriptor

        weight = _find_weight()
        if weight is None:
            raise FileNotFoundError("RealESRGAN_x4plus.pth не найден")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = ModelLoader().load_from_file(weight)
        if not isinstance(model, ImageModelDescriptor):
            raise RuntimeError("Файл модели не распознан как image model")
        model = model.to(device).eval()

        work = image.convert("RGB")
        max_side = 900
        w, h = work.size
        scale = min(max_side / max(w, h), 1.0)
        work = work.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

        arr = np.asarray(work).astype(np.float32) / 255.0
        tensor = torch.from_numpy(arr).permute(2,0,1).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(tensor)

        output = output.squeeze(0).clamp(0,1).permute(1,2,0).cpu().numpy()
        out = Image.fromarray((output*255).round().astype(np.uint8))
        out = _resize_2k(out)

        path = os.path.join(EXPORT_DIR, "realphoto_2k.png")
        out.save(path)
        return out, path, "✓ Real-ESRGAN 2K выполнен"

    except Exception as e:
        out = _resize_2k(image)
        path = os.path.join(EXPORT_DIR, "realphoto_2k_fallback.png")
        out.save(path)
        return out, path, f"2K fallback выполнен ({e})"
