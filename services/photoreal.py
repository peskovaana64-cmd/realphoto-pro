import gc
import os
import cv2
import numpy as np
import torch
from PIL import Image, ImageEnhance

_PIPE = None

def _cleanup():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def _feather_mask(h, w, border=96):
    y = np.ones(h, dtype=np.float32)
    x = np.ones(w, dtype=np.float32)
    b = min(border, h // 2, w // 2)
    if b > 0:
        ramp = np.linspace(0.05, 1.0, b, dtype=np.float32)
        y[:b] = ramp
        y[-b:] = ramp[::-1]
        x[:b] = ramp
        x[-b:] = ramp[::-1]
    return (y[:, None] * x[None, :])[:, :, None]

def _restore_microdetails(original, processed, amount=0.55):
    orig = np.array(original.convert("RGB")).astype(np.float32)
    proc = np.array(processed.convert("RGB")).astype(np.float32)
    blur = cv2.GaussianBlur(orig, (0, 0), 1.0)
    high = orig - blur
    final = np.clip(proc + high * amount, 0, 255).astype(np.uint8)
    return Image.fromarray(final)

def _load_pipeline():
    global _PIPE
    if _PIPE is not None:
        return _PIPE

    from diffusers import StableDiffusionControlNetImg2ImgPipeline, ControlNetModel

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    controlnet = ControlNetModel.from_pretrained(
        os.getenv("CONTROLNET_MODEL", "lllyasviel/control_v11f1e_sd15_tile"),
        torch_dtype=dtype,
    )

    pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
        os.getenv("BASE_MODEL", "SG161222/Realistic_Vision_V5.1_noVAE"),
        controlnet=controlnet,
        torch_dtype=dtype,
        safety_checker=None,
    )

    pipe = pipe.to(device)

    try:
        pipe.enable_xformers_memory_efficient_attention()
    except Exception:
        pass

    pipe.enable_attention_slicing()
    _PIPE = pipe
    return _PIPE

def _preset(mode):
    if mode == "Мягко":
        return dict(denoise=0.08, blend=0.24, steps=16, guidance=3.8)
    if mode == "Мощно":
        return dict(denoise=0.12, blend=0.40, steps=20, guidance=4.2)
    return dict(denoise=0.10, blend=0.34, steps=18, guidance=4.0)

def photoreal_pass(
    image,
    mode="Сбалансировано",
    protect_person=True,
    protect_architecture=True,
    preserve_text=True,
    realism_strength=0.50,
    restore_details=0.55,
    sharpness=0.20,
):
    """
    Бесплатный tiled img2img pass.
    Он не заменяет коммерческие image-edit модели, но даёт максимально
    безопасную обработку на доступном open-source стеке.
    """
    pipe = _load_pipeline()

    original = image.convert("RGB")
    W, H = original.size

    tile = 512
    overlap = 128
    step = tile - overlap

    p = _preset(mode)
    denoise = p["denoise"] + (realism_strength - 0.5) * 0.06
    blend = p["blend"]
    control = 1.0

    if protect_architecture:
        denoise -= 0.015
        blend -= 0.06
        control += 0.10
    if preserve_text:
        denoise -= 0.01
        blend -= 0.05
        control += 0.10
    if protect_person:
        denoise -= 0.01
        blend -= 0.04

    denoise = float(np.clip(denoise, 0.05, 0.16))
    blend = float(np.clip(blend, 0.18, 0.42))
    control = float(np.clip(control, 0.85, 1.20))

    xs = list(range(0, max(W - tile, 0) + 1, step))
    ys = list(range(0, max(H - tile, 0) + 1, step))
    if not xs or xs[-1] != max(W - tile, 0):
        xs.append(max(W - tile, 0))
    if not ys or ys[-1] != max(H - tile, 0):
        ys.append(max(H - tile, 0))
    xs = sorted(set(xs))
    ys = sorted(set(ys))

    canvas = np.zeros((H, W, 3), dtype=np.float32)
    weights = np.zeros((H, W, 1), dtype=np.float32)
    mask = _feather_mask(tile, tile)

    prompt = """
real professional photograph, same exact scene, same camera angle,
same framing, same architecture, same people positions,
physically realistic materials, real stone texture, believable glass,
natural skin texture, natural hair, real fabric fibers,
realistic reflections, photographic dynamic range,
subtle real-world imperfections, fine authentic detail
"""
    if protect_architecture:
        prompt += ", preserve columns, windows, facade rhythm, building geometry"
    if preserve_text:
        prompt += ", preserve readable signs, banners and logos"
    if protect_person:
        prompt += ", preserve the same person's identity, pose, hairstyle and clothing"

    negative = """
cgi, 3d render, illustration, painting, cartoon, plastic skin, wax skin,
doll face, beauty filter, changed identity, distorted face, bad hands,
redesigned architecture, warped windows, warped columns, unreadable text,
broken logo, oversaturated, hdr, heavy blur, overprocessed
"""

    device = "cuda" if torch.cuda.is_available() else "cpu"
    generator = torch.Generator(device=device).manual_seed(42)

    for y in ys:
        for x in xs:
            crop = original.crop((x, y, x + tile, y + tile))
            result = pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=crop,
                control_image=crop,
                strength=denoise,
                controlnet_conditioning_scale=control,
                guidance_scale=p["guidance"],
                num_inference_steps=p["steps"],
                generator=generator,
            ).images[0]

            result = Image.blend(crop, result, blend)
            arr = np.array(result).astype(np.float32)
            h, w = arr.shape[:2]
            m = mask[:h, :w]
            canvas[y:y+h, x:x+w] += arr * m
            weights[y:y+h, x:x+w] += m
            _cleanup()

    weights = np.maximum(weights, 1e-6)
    final = np.clip(canvas / weights, 0, 255).astype(np.uint8)
    final = Image.fromarray(final)
    final = _restore_microdetails(original, final, amount=float(np.clip(restore_details, 0.25, 0.85)))
    final = ImageEnhance.Sharpness(final).enhance(1.0 + sharpness * 1.5)

    return final
