# REALPHOTO PRO

Прототип сервиса для перевода готовых CGI / AI / 3D-кадров в более фотографичный вид
с максимальным сохранением исходной архитектуры, композиции, людей, текста и логотипов.

## Что уже реализовано

- Gradio web UI.
- Режимы: Мягко / Сбалансировано / Мощно.
- Защита человека.
- Усиленная защита архитектуры.
- Защита текста и логотипов.
- Бесплатный tiled photoreal pass:
  - Realistic Vision 5.1
  - ControlNet Tile
  - overlap/feather stitching
  - возврат исходных микродеталей.
- Экспорт 2K.
- Интеграционная точка Real-ESRGAN через Spandrel.
- Интеграционные точки для:
  - CodeFormer
  - Magnific
  - Nano Banana
  - GPT Image.

## Важное ограничение

Open-source pipeline является бесплатной базовой версией и не гарантирует качество
на уровне современных коммерческих image-edit моделей.

Для production рекомендуется сохранить этот pipeline как `Free / Local` режим и добавить
платные провайдеры как `Pro` режимы:

1. Nano Banana / Gemini image editing
2. GPT Image editing
3. Magnific
4. корпоративный GPU backend

---

# Локальный запуск

Python 3.11/3.12 рекомендуется.

```bash
pip install -r requirements.txt
python app.py
```

Сайт:
`http://localhost:8080`

---

# Docker

```bash
docker build -t realphoto-pro .
docker run --gpus all -p 8080:8080 realphoto-pro
```

---

# Google Cloud Run GPU — production handoff

## Рекомендуемая схема

- GitHub → исходный код
- Artifact Registry → Docker image
- Cloud Run GPU → backend
- Gradio сейчас можно оставить как UI или позднее заменить React/Next.js
- Cloud Storage → результаты
- Secret Manager → API keys

## Важно

Для Cloud Run GPU потребуется включённый billing и доступная GPU quota в выбранном регионе.

Пример логики деплоя для техотдела:

```bash
gcloud builds submit \
  --tag REGION-docker.pkg.dev/PROJECT_ID/realphoto/realphoto-pro:latest
```

Далее создать Cloud Run service из образа и включить GPU через настройки Cloud Run.

Точный `gcloud run deploy` лучше формировать уже под:
- Project ID
- регион
- тип GPU
- лимиты памяти
- корпоративные политики.

---

# Модели

По умолчанию:

```text
BASE_MODEL=SG161222/Realistic_Vision_V5.1_noVAE
CONTROLNET_MODEL=lllyasviel/control_v11f1e_sd15_tile
```

Модели Hugging Face скачиваются при первом запуске.

## Real-ESRGAN

Вес:

```text
RealESRGAN_x4plus.pth
```

не включён в репозиторий/ZIP из-за размера.

Его нужно положить в:

```text
models/RealESRGAN_x4plus.pth
```

или задать путь:

```text
REALESRGAN_MODEL=/path/to/RealESRGAN_x4plus.pth
```

---

# Внешние API

## Nano Banana

Переменная:

```text
GEMINI_API_KEY
```

Техотдел должен реализовать вызов в:

```text
services/external_providers.py
```

## GPT Image

Переменная:

```text
OPENAI_API_KEY
```

Вызов реализуется там же.

## Magnific

Переменная:

```text
MAGNIFIC_API_KEY
```

API-коннектор зависит от доступного Magnific API/контракта.

---

# Рекомендуемая production-архитектура

```text
Browser
   ↓
Frontend
   ↓
API / Queue
   ├── Free pipeline
   │      ├── Tiled photoreal
   │      ├── Face restore
   │      └── Real-ESRGAN
   │
   └── Pro providers
          ├── Nano Banana
          ├── GPT Image
          └── Magnific
   ↓
Object Storage
   ↓
Result URL
```

Для нескольких пользователей обработку желательно вынести в очередь задач,
а не держать один Gradio worker на одном GPU.

---

# Что техотделу стоит сделать первым

1. Разместить репозиторий в корпоративном GitHub.
2. Настроить Docker build.
3. Развернуть GPU backend.
4. Подключить постоянное хранилище результатов.
5. Перенести секреты в Secret Manager.
6. Подключить платные providers.
7. Добавить очередь.
8. При необходимости заменить Gradio на корпоративный frontend.
