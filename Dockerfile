FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# keep the database in /data so it can be a volume and survive restarts
ENV WATCHSHELF_DB=/data/database.db
VOLUME /data

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]