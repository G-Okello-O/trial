# Base image with Python installed
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.6.1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl build-essential libpq-dev

# Install Poetry using the official installation script
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy Poetry dependency files
COPY pyproject.toml poetry.lock* /app/

# Install dependencies without dev packages and root
RUN poetry install --no-root --no-dev

# Copy the rest of the application code
COPY . /app/

# Expose port (default to 8000)
EXPOSE ${PORT}

# Command to run the app with Poetry and Chainlit, evaluating environment variable for PORT
CMD sh -c "poetry run chainlit run main.py --host=0.0.0.0 --port=${PORT}"
