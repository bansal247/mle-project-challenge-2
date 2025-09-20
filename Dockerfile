# Use Miniconda base image
FROM continuumio/miniconda3:latest

# Disable Python output buffering
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy Conda environment and create it
COPY conda_environment.yml .
RUN conda env create -f conda_environment.yml

# Activate Conda environment in all RUN commands
SHELL ["/bin/bash", "-c"]

# Install optional pip packages
COPY requirements.txt .
RUN source activate housing && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start Gunicorn with Uvicorn workers and real-time logging
CMD source activate housing && \
    gunicorn -k uvicorn.workers.UvicornWorker app:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance
