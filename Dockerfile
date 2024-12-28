# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app/app.py

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 3000 (matches the port in docker-compose.yml)
EXPOSE 3000

# Command to run the application
# Runs app.py
CMD ["python", "-m", "flask", "--app", "main.py", "run", "--host=0.0.0.0", "--port=3000"]
