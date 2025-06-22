# Stage 1: Build stage
FROM python:3.10-slim AS builder

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Create a virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Stage 2: Final stage
FROM python:3.10-slim

# Set the working directory to /app/Example
WORKDIR /app/Example

# Copy only the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code into the Example directory
COPY . .

# Set the environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=DEBUG
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]