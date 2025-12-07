# Specify the base image
FROM python:3.13
# Set environment variables
# Avoid writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1 \
PIP_DISABLE_PIP_VERSION_CHECK=on
# Create and set working directory
WORKDIR /app
# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
pip install -r requirements.txt
# Copy project files
COPY . .
# Expose the Django port
EXPOSE 8000