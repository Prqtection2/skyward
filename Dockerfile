# Use Ubuntu base image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    unzip \
    xvfb \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install chromedriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+") \
    && MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${MAJOR_VERSION}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 10000

# Start command
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 & gunicorn --bind 0.0.0.0:10000 app:app"]
