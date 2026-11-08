FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py parsers.py ./
COPY templates ./templates
USER nobody
CMD exec gunicorn --bind ":${PORT:-8080}" --workers 1 --threads 4 --timeout 30 "main:production_app()"
