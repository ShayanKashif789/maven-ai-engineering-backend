# ================================
# Base Image
# ================================
FROM python:3.11-slim

# ================================
# Working Directory
# ================================
WORKDIR /workspace

# ================================
# Environment Variables
# ================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ================================
# System Dependencies
# ================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ================================
# Python Dependencies
# ================================
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --default-timeout=3000 --no-cache-dir -r requirements.txt

# ================================
# NLTK Data
# ================================
RUN python -m nltk.downloader punkt stopwords

# ================================
# Jupyter Config
# ================================
RUN jupyter lab --generate-config && \
    echo "c.ServerApp.token = ''" >> ~/.jupyter/jupyter_lab_config.py && \
    echo "c.ServerApp.password = ''" >> ~/.jupyter/jupyter_lab_config.py && \
    echo "c.ServerApp.allow_origin = '*'" >> ~/.jupyter/jupyter_lab_config.py && \
    echo "c.ServerApp.ip = '0.0.0.0'" >> ~/.jupyter/jupyter_lab_config.py

# ================================
# Project Files
# ================================
COPY . .

# ================================
# Expose Ports
# ================================
EXPOSE 8888 8501 8000

# ================================
# Default (will be overridden)
# ================================
CMD ["bash"]
