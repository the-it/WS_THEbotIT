# Use an official Python runtime as a parent image
FROM python:3.14-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Install a C toolchain: some dependencies (e.g. mwparserfromhell) have no
# prebuilt wheel for this Python/arch and are compiled from source by uv sync.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies from pyproject.toml / uv.lock
RUN pip install uv
RUN uv sync
