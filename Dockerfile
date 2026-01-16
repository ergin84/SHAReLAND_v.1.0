FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including GDAL for PostGIS
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gdal-bin \
    libgdal-dev \
    python3-dev \
    gcc \
    build-essential \
    libz-dev \
    libjpeg-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY shareland/requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY shareland/ /app/

# Create directories for media and static files
RUN mkdir -p /app/media /app/static

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD python manage.py runserver 0.0.0.0:8000
