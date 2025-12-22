FROM python:3.11-slim

# Prevent Python from buffering stdout and stderr
ENV  PYTHONUNBUFFERED=1

# Install system dependencies 
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-dev \
    bluez \
    dbus \
    wireless-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]