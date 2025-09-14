#!/usr/bin/env bash
# Build script for Render deployment

set -e  # Exit on error

echo "=== Starting Render build process ==="

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python -m flask db upgrade

echo "=== Build complete! ==="