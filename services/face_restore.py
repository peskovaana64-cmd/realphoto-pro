import os
from PIL import Image

def restore_face(image, fidelity=0.85):
    """
    Точка интеграции CodeFormer.
    В контейнере по умолчанию выключена, чтобы не тянуть большой репозиторий
    без необходимости. Техотдел может подключить CodeFormer как отдельный
    сервис/контейнер или заменить на собственный face-restoration backend.
    """
    return image, "Face enhancement: модуль подготовлен, CodeFormer backend нужно подключить при деплое."
