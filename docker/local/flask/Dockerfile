# Specify a base image for the container
FROM python:3.9.9-slim-buster

LABEL name="bookstore-api"
LABEL license="MIT"
LABEL description="Development image for Bookstore API"
LABEL maintainer="sendi.stev@gmail.com"

# Set environment variables
ENV APP_HOME=/app
RUN mkdir -p $APP_HOME
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

# Specify the working directory
WORKDIR $APP_HOME

# Install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    passwd \
    && rm -rf /var/lib/apt/lists/*

# Create a non root user
RUN groupadd -r flask && useradd --no-log-init -r -g flask flask

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and change ownership
COPY --chown=flask:flask . ${APP_HOME}

# Prepare client secret with secure permissions
COPY --chown=flask:flask  client_secret.json ${APP_HOME}/client_secret.json
RUN chmod 600 ${APP_HOME}/client_secret.json

# Switch to the non root user
USER flask

# Expose Flask's default port
EXPOSE 5000

# Run the flask app
CMD ["python", "run.py", "--host=0.0.0.0"]