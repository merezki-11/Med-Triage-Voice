# Use the official lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /usr/src/app

# Install system dependencies (ffmpeg is CRITICAL for Whisper audio decoding)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker build cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# IMPORTANT: Download the Whisper model during the build phase!
# If we don't do this, the Cloud Run container will try to download it on the first voice recording,
# which causes HuggingFace to block the IP with a "429 Too Many Requests" error due to shared Google IPs.
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"

# Copy the rest of the application
COPY . .

# Expose port 8080 (Google Cloud Run default port)
EXPOSE 8080

# Launch FastAPI via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
