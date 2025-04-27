# Use the official Python image from the Docker Hub
FROM python:3.13-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies if there's a requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command to run your script
CMD ["python", "src/CissUsbForPython3.py"]