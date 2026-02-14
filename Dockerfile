# Use Python base image with Java support
FROM python:3.11-slim

# Install Java (required for APK tools)
RUN apt-get update && \
    apt-get install -y default-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Verify Java installation
RUN java -version

# Expose port for Render
EXPOSE 10000

# Run bot
CMD ["python", "firebase_apk_bot.py"]
