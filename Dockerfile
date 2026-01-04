# Use the official Python image from the Docker Hub
FROM python:3.13-alpine

# Set the working directory in the container
WORKDIR /app

# Update first
RUN apk update \
    && apk upgrade \
    && apk add --no-cache libpq

# Install psycopg2 dependencies
RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev
RUN apk update && \
    apk add --virtual build-deps

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy the current directory contents into the container at /app
COPY . /app

# Create virtual environment and install dependencies from requirements.txt using UV
RUN uv venv && uv pip install -r requirements.txt

# Set the default command to run your script using UV
CMD ["uv", "run", "python", "src/CissUsbForPython3.py"]