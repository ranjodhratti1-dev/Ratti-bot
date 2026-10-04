FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python libraries directly
RUN pip install --no-cache-dir requests gTTS

COPY . .

CMD ["python", "main.py"]
