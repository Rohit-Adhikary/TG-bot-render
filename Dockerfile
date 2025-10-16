FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create and set proper permissions for data directory
RUN mkdir -p /app/data && \
    chmod 755 /app/data

# Create users.json with proper permissions
RUN echo '{}' > users.json && \
    chmod 666 users.json

# Switch to non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Expose port (Render uses $PORT)
EXPOSE 8080

# Start the bot
CMD ["python", "index.py"]
