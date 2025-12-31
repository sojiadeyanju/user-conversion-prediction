# --- Stage 1: Builder ---
# We use a larger image to build/install dependencies
FROM python:3.9-slim AS builder

WORKDIR /app

# Set environment variables to keep things clean
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies into a specific folder (/install)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --- Stage 2: Final Image ---
# We switch to a fresh, empty slim image
FROM python:3.9-slim

WORKDIR /app

# Copy ONLY the installed library files from the builder stage
COPY --from=builder /install /usr/local

# Copy your actual application code (ignoring what's in .dockerignore)
COPY . .

# Expose port
EXPOSE 5001

# Run
CMD ["python", "app.py"]