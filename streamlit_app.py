import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io

st.set_page_config(
    page_title="REALPHOTO PRO",
    page_icon="📷",
    layout="wide"
)

st.title("REALPHOTO PRO")
st.subheader("Render → Real Photograph")

st.write(
    """
Бесплатная веб-версия интерфейса для обработки готовых CGI / AI / 3D кадров.

Сейчас сайт работает в лёгком режиме без GPU:
- сохраняет исходное изображение;
- делает мягкую фото-коррекцию;
- усиливает микроконтраст;
- добавляет умеренную резкость;
- экспортирует результат в 2K.

Тяжёлые AI-модули:
- Photoreal AI
- Magnific
- Nano Banana
- GPT Image
- CodeFormer
- Real-ESRGAN GPU

предназначены для дальнейшего подключения техотделом.
"""
)

uploaded_file = st.file_uploader(
    "Загрузите изображение",
    type=["png", "jpg", "jpeg", "webp"]
)

st.markdown("### Режим обработки")

mode = st.radio(
    "Выберите режим",
    ["Мягко", "Сбалансировано", "Мощно"],
    horizontal=True
)

st.markdown("### Защита сцены")

col1, col2, col3 = st.columns(3)

with col1:
    protect_person = st.checkbox(
        "Защитить человека",
        value=True
    )

with col2:
    protect_architecture = st.checkbox(
        "Максимум архитектуры",
        value=True
    )

with col3:
    preserve_text = st.checkbox(
        "Сохранить текст и логотипы",
        value=True
    )

st.markdown("### Точная настройка")

realism_strength = st.slider(
    "Сила обработки",
    min_value=0.0,
    max_value=1.0,
    value=0.45,
    step=0.05
)

detail_strength = st.slider(
    "Микродетали",
    min_value=0.0,
    max_value=1.0,
    value=0.50,
    step=0.05
)

sharpness_strength = st.slider(
    "Финальная резкость",
    min_value=0.0,
    max_value=1.0,
    value=0.25,
    step=0.05
)

st.markdown("### Дополнительные модули")

col4, col5, col6 = st.columns(3)

with col4:
    st.checkbox(
        "Magnific",
        value=False,
        disabled=True
    )

with col5:
    st.checkbox(
        "Nano Banana",
        value=False,
        disabled=True
    )

with col6:
    st.checkbox(
        "GPT Image",
        value=False,
        disabled=True
    )

def light_photo_pass(image, mode, realism, detail, sharpness):
    result = image.convert("RGB")

    if mode == "Мягко":
        contrast = 1.02
        color = 0.99
        sharp = 1.05

    elif mode == "Мощно":
        contrast = 1.08
        color = 0.98
        sharp = 1.18

    else:
        contrast = 1.05
        color = 0.99
        sharp = 1.10

    contrast += realism * 0.03
    sharp += sharpness * 0.25

    result = ImageEnhance.Contrast(result).enhance(contrast)
    result = ImageEnhance.Color(result).enhance(color)
    result = ImageEnhance.Sharpness(result).enhance(sharp)

    if detail > 0:
        result = result.filter(
            ImageFilter.UnsharpMask(
                radius=1.0,
                percent=int(40 + detail * 80),
                threshold=4
            )
        )

    return result

def resize_2k(image):
    w, h = image.size
    scale = 2048 / max(w, h)

    new_w = int(w * scale)
    new_h = int(h * scale)

    return image.resize(
        (new_w, new_h),
        Image.LANCZOS
    )

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    st.markdown("### До / После")

    original_col, result_col = st.columns(2)

    with original_col:
        st.image(
            image,
            caption="Исходное изображение",
            use_container_width=True
        )

    if st.button(
        "СДЕЛАТЬ ФОТОГРАФИЕЙ",
        type="primary",
        use_container_width=True
    ):
        result = light_photo_pass(
            image,
            mode,
            realism_strength,
            detail_strength,
            sharpness_strength
        )

        st.session_state["result"] = result

    if "result" in st.session_state:
        result = st.session_state["result"]

        with result_col:
            st.image(
                result,
                caption="Результат",
                use_container_width=True
            )

        result_2k = resize_2k(result)

        buffer = io.BytesIO()
        result_2k.save(
            buffer,
            format="PNG"
        )

        st.download_button(
            label="СКАЧАТЬ 2K",
            data=buffer.getvalue(),
            file_name="realphoto_pro_2k.png",
            mime="image/png",
            use_container_width=True
        )

        st.info(
            "Это облегчённая бесплатная версия. "
            "Полный AI photoreal backend подключается отдельно."
        )

else:
    st.info("Загрузите изображение, чтобы начать обработку.")
