# Use a slim Python image to save hundreds of megabytes in the base image
FROM python:3.12-slim

# Set environment variables
# Avoid writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Create and set working directory
WORKDIR /app

# Install system dependencies required for ML packages (like gcc) if needed.
# Since python:3.13-slim might not have build tools, we install them temporarily,
# build/install the wheels, and then remove the build tools to keep the image small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

# Use --no-cache-dir to avoid storing downloaded pip packages in the docker image layers
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to save space after installing python packages
RUN apt-get purge -y --auto-remove build-essential

# Copy project files
COPY . .

# Run collectstatic to gather static files before deployment
RUN python manage.py collectstatic --noinput

# Expose the Django port
EXPOSE 8000
