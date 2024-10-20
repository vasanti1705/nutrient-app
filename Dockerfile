# Use the official Python base image
FROM python:latest

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script and other necessary files to the container
COPY nutient.py /app/nutient.py
COPY requirements.txt /app/requirements.txt

# Install necessary Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Flask will use
EXPOSE 5000

# Command to run the Flask application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "nutient:app"]
