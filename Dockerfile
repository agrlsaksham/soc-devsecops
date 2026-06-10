FROM python:3.10-slim

# Create app directory
WORKDIR /app

# Create a non-root group and user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy application files
COPY app/ .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create the logs directory and grant ownership to non-root user
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

# Expose port
EXPOSE 5000

# Set user
USER appuser

# Start application
CMD ["python", "app.py"]