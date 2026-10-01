import os
import gc
import gradio as gr
from PIL import Image

from services.photoreal import photoreal_pass
from services.upscale import upscale_2k
from services.face_restore import restore_face
from services.external_providers import (
    external_status,
    run_magnific,
    run_nano_banana,
    run_gpt_image,
)

APP_TITLE = "REALPHOTO PRO"

def process(
    image,
    mode,
    protect_person,
    protect_architecture,
    preserve_text,
    realism_strength,
    restore_details,
    sharpness,
    face_enhancement,
    use_upscale,
    use_magnific,
    use_nano,
    use_gpt,
):
    if image is None:
        return None, None, "Загрузите изображение."

    result = photoreal_pass(
        image=image,
        mode=mode,
        protect_person=protect_person,
        protect_architecture=protect_architecture,
        preserve_text=preserve_text,
        realism_strength=realism_strength,
        restore_details=restore_details,
        sharpness=sharpness,
    )

    log = ["✓ Бесплатный photoreal pass выполнен"]

    if face_enhancement:
        result, msg = restore_face(result)
        log.append(msg)

    # Платные/внешние провайдеры — заглушки до подключения ключей.
    if use_magnific:
        result, msg = run_magnific(result)
        log.append(msg)

    if use_nano:
        result, msg = run_nano_banana(result)
        log.append(msg)

    if use_gpt:
        result, msg = run_gpt_image(result)
        log.append(msg)

    export_path = None
    if use_upscale:
        result, export_path, msg = upscale_2k(result)
        log.append(msg)

    gc.collect()

    return result, export_path, "\n".join(log)


with gr.Blocks(title=APP_TITLE, theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
# REALPHOTO PRO
### Render → Real Photograph

Обработка готовых CGI / AI / 3D кадров с приоритетом:
- сохранения архитектуры;
- сохранения композиции;
- сохранения текста и логотипов;
- естественной фактуры материалов;
- фотореалистичного света;
- аккуратного улучшения людей;
- экспорта в 2K.
        """
    )

    with gr.Row():
        input_image = gr.Image(type="pil", label="Исходное изображение")
        output_image = gr.Image(type="pil", label="Результат")

    mode = gr.Radio(
        ["Мягко", "Сбалансировано", "Мощно"],
        value="Сбалансировано",
        label="Режим",
    )

    with gr.Row():
        protect_person = gr.Checkbox(True, label="Защитить человека")
        protect_architecture = gr.Checkbox(True, label="Максимум архитектуры")
        preserve_text = gr.Checkbox(True, label="Сохранить текст и логотипы")

    with gr.Row():
        realism_strength = gr.Slider(0, 1, 0.50, step=0.01, label="Сила realism-pass")
        restore_details = gr.Slider(0, 1, 0.55, step=0.01, label="Возврат исходных микродеталей")
        sharpness = gr.Slider(0, 1, 0.20, step=0.01, label="Финальная резкость")

    gr.Markdown("## Бесплатные модули")
    with gr.Row():
        face_enhancement = gr.Checkbox(False, label="Face enhancement")
        use_upscale = gr.Checkbox(True, label="AI Upscale 2K")

    gr.Markdown("## Внешние модули для техотдела")
    with gr.Row():
        use_magnific = gr.Checkbox(False, label="Magnific")
        use_nano = gr.Checkbox(False, label="Nano Banana")
        use_gpt = gr.Checkbox(False, label="GPT Image")

    run_btn = gr.Button("СДЕЛАТЬ ФОТОГРАФИЕЙ", variant="primary")
    export_file = gr.File(label="Файл результата")
    status = gr.Textbox(label="Статус", lines=8)

    gr.Markdown(external_status())

    run_btn.click(
        fn=process,
        inputs=[
            input_image,
            mode,
            protect_person,
            protect_architecture,
            preserve_text,
            realism_strength,
            restore_details,
            sharpness,
            face_enhancement,
            use_upscale,
            use_magnific,
            use_nano,
            use_gpt,
        ],
        outputs=[output_image, export_file, status],
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=port,
        show_api=False,
    )
