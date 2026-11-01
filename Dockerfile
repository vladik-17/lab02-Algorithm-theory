FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Moscow

# Tk выводит окно через X11/WSLg. Xvfb нужен для проверки без экрана.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tk fonts-dejavu-core xvfb xauth \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import tkinter; print('Tk', tkinter.TkVersion)"

COPY energy_calculator ./energy_calculator
COPY main.py ./
COPY tests ./tests

RUN mkdir -p /app/data /app/exports

CMD ["python", "main.py"]
