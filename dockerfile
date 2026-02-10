# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RUN_ENV=test
ENV REPORT=no

# Set work directory
WORKDIR /app

# Install system dependencies
# Build tools: build-essential, libssl-dev, etc. for compiling Python packages (like cryptography) if wheels are missing
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Default command to run tests in a container (no HTML report generation)
CMD ["python", "run.py", "-env", "test", "-report", "no"]
