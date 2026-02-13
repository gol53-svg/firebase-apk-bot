# Use Python base image with Java
FROM python:3.11-slim

# Install Java
RUN apt-get update && \
    apt-get install -y default-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Verify Java installation
RUN java -version

# Run the bot
CMD ["python", "firebase_apk_bot.py"]
