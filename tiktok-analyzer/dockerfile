FROM python:3.12-slim

WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Создаём папку для данных (на случай, если volume не подключён)
RUN mkdir -p /app/data

CMD ["python", "raspisanie.py"]
