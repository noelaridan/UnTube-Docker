# Use an official Python runtime as the base image
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file to the container
COPY ./webapp/requirements.txt /app/requirements.txt

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY ./webapp /app

# Running Django migrations
RUN python manage.py migrate

# Set the environment variable to run the application using the production settings
ENV PYTHONPATH=/app

# Expose the default Django port
EXPOSE 8000

# Define the command to run the application
CMD [ "python", "./manage.py", "runserver", "0.0.0.0:8000" ]
