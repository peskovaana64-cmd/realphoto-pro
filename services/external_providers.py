def external_status():
    return """
> **Внешние провайдеры:** интерфейс уже содержит точки подключения Magnific, Nano Banana и GPT Image.
> До добавления API-ключей эти переключатели являются заглушками.
"""

def run_magnific(image):
    return image, "Magnific: требуется реализация API-клиента техотделом."

def run_nano_banana(image):
    return image, "Nano Banana: требуется GEMINI_API_KEY + оплачиваемый Gemini API."

def run_gpt_image(image):
    return image, "GPT Image: требуется OPENAI_API_KEY и реализация image-edit вызова."
