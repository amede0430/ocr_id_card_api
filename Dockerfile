# Use an official Python runtime as a parent image
FROM python:3.10.8

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install  -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 8000 for the Django app to run on
EXPOSE 8000

# Run the migrations and then start the Django server
CMD ["python","manage.py","runserver","0.0.0.0:8000"]
