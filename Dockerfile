FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

RUN useradd --create-home --uid 1000 --user-group bot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py config.json ./
RUN chown -R bot:bot /app

USER bot

CMD ["python", "bot.py"]
