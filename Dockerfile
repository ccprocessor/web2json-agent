# Apify Dockerfile for web2json-agent
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /usr/src/app

# Copy project files
COPY . ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /usr/src/app/apify_storage/datasets/default

# Set environment variable for Apify
ENV APIFY_CONTAINER_URL=http://127.0.0.1:${APIFY_CONTAINER_PORT} \
    APIFY_DEFAULT_DATASET_ID=default

# Entry point script
COPY docker_entrypoint.py ./

# Run the actor
CMD ["python", "docker_entrypoint.py"]
