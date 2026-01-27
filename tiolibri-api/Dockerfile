# Base image: Python 3.11 on Debian Bookworm
FROM python:3.11-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for WeasyPrint
# Cairo: 2D graphics library
# Pango: text layout and rendering
# GObject: object system for GLib
# GdkPixbuf: image loading library
# libffi-dev: Foreign Function Interface library
# shared-mime-info: MIME type detection
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Run FastAPI with uvicorn
# Railway provides $PORT dynamically, fallback to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

