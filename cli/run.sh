#!/bin/bash
# Eigen3-SF CLI Launcher

# Function to install dependencies
install() {
    echo "Installing dependencies..."
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt
    echo "Installation complete!"
}

# Check for install command
if [ "$1" = "install" ]; then
    install
    exit 0
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Using existing virtual environment..."
    source venv/bin/activate
fi

# Run the CLI
python main.py "$@"
