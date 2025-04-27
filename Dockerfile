# Use the official Python image from the Docker Hub
FROM python:3.13-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Update first
RUN apk update \
    && apk upgrade \
    && apk add --no-cache libpq

# Install psycopg2 dependencies
RUN apk add --no-cache postgresql-dev gcc python3-dev musl-dev
RUN apk update && \
    apk add --virtual build-deps

RUN pip install psycopg2
# Install any needed packages specified in requirements.txt

# Install dependencies if there's a requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command to run your script
CMD ["python", "src/CissUsbForPython3.py"]