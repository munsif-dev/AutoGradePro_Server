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

# Run the application
CMD ["gunicorn", "--timeout", "1800", "--bind", "0.0.0.0:8000", "Server.wsgi:application"]