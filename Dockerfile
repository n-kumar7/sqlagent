# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install netcat for entrypoint script (nc command)
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Set environment variables for Python using key=value syntax
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory to /app
WORKDIR /app

# Copy the local wheel file and install your app package
# Ensure the wheel file exists in the "dist" folder (e.g., my_app-0.1.0-py3-none-any.whl)
COPY dist/my_app-0.1.0-py3-none-any.whl /tmp/
RUN pip install /tmp/my_app-0.1.0-py3-none-any.whl

# Copy the remaining application code (optional, if needed for data files, etc.)
COPY . /app/

# Expose any ports if needed (for example, if your app exposes metrics)
# EXPOSE 8000

# Run the main application
CMD ["python", "-m", "app.main"]
