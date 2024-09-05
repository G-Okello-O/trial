# Use the latest Python image from the official Docker hub
FROM python:latest

# Set environment variables to prevent Python from writing .pyc files
# and to ensure that Python outputs everything to the console
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy only the Poetry configuration files first
COPY pyproject.toml poetry.lock* /app/

# Install dependencies using Poetry
RUN poetry install --no-root --no-dev

# Copy the rest of the application code
COPY . /app/

# Command to run on container start
CMD ["poetry", "run", "chainlit", "run", "main.py"]
