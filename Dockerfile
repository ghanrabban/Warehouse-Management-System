# Dockerfile for Barcode WMS App

# 1. Base image: Python 3.10 slim
FROM python:3.10-slim

# 2. Set working directory
WORKDIR /app

# 3. Install OS‑level dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libjpeg-dev \
        zlib1g-dev \
        default-libmysqlclient-dev \
        libserial-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY barcode_menu.py .

# 6. Default command: run the interactive menu
ENTRYPOINT ["python", "barcode_menu.py"]
