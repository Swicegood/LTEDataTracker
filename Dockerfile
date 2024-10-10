# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir requests schedule

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV NAME LTETracker

# Run script.py when the container launches
CMD ["python", "./lte_data_tracker.py"]