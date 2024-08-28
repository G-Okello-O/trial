# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies with Poetry
RUN poetry install --no-dev

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Copy the environment check script
COPY check_env.sh /app/check_env.sh

# Make the script executable
RUN chmod +x /app/check_env.sh

# Run the environment check script and then run the app
CMD ["/bin/bash", "-c", "/app/check_env.sh && poetry run chainlit run main.py --port 8000"]
