FROM python:3.12-slim

WORKDIR /app

# Install yt-dlp system dependency (ffmpeg optional but useful)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

CMD ["python", "run.py"]
