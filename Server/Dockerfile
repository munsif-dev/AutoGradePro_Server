# Base Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn numpy pillow

# Copy project
COPY . .

# Create directory for media files
RUN mkdir -p /app/media
RUN mkdir -p /app/static


# Add the patches file
COPY patches.py /app/
RUN echo 'import patches' >> /app/Server/wsgi.py


COPY preload_model.py /app/


# Add timeout parameters to preload_model.py
RUN sed -i 's/timeout=300/timeout=600/g' /app/preload_model.py


# Set environment variables for timeouts
ENV OLLAMA_TIMEOUT=60.0
ENV GUNICORN_TIMEOUT=300


CMD bash -c "python preload_model.py && gunicorn --preload --bind 0.0.0.0:8000 --workers 3 --worker-class gthread --threads 4 --timeout ${GUNICORN_TIMEOUT} --graceful-timeout ${GUNICORN_TIMEOUT} --worker-tmp-dir /dev/shm --keep-alive 65 --log-level debug Server.wsgi:application"