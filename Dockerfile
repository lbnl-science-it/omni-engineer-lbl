FROM python:3-slim

# Install git
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Clone the application code from GitHub
ARG REPO_URL=https://github.com/lbnl-science-it/omni-engineer-lbl
ARG REPO_BRANCH=utilities
RUN git clone -b ${REPO_BRANCH} ${REPO_URL} /app

# Install Python dependencies
RUN if [ -f "/app/requirements.txt" ]; then \
        pip install --no-cache-dir -r /app/requirements.txt; \
    fi

# Copy the entrypoint script into the image
COPY entrypoint.sh /entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /entrypoint.sh

# Use the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Default command to run your application
CMD ["python", "main.py"]

