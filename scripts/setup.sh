#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to handle errors
handle_error() {
    print_message "Error: $1" "$RED"
    exit 1
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_message "This script should not be run as root." "$YELLOW"
    exit 1
fi

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)     OS_TYPE=linux;;
    Darwin*)    OS_TYPE=macos;;
    CYGWIN*)    OS_TYPE=windows;;
    MINGW*)     OS_TYPE=windows;;
    *)          OS_TYPE="unknown"
esac

print_message "Detected OS: $OS_TYPE" "$GREEN"

# Project variables
PROJECT_NAME="Project"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
PYTHON_VERSION="3.8"

print_message "Setting up $PROJECT_NAME..." "$GREEN"
print_message "Project directory: $PROJECT_DIR" "$GREEN"

# Check for Python
if ! command_exists python3; then
    handle_error "Python3 is not installed. Please install Python $PYTHON_VERSION or higher."
fi

# Check Python version
PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ $(echo "$PYTHON_VER >= $PYTHON_VERSION" | bc -l 2>/dev/null || echo "0") -eq 0 ]]; then
    handle_error "Python $PYTHON_VERSION or higher is required. Found $PYTHON_VER"
fi

print_message "Python version: $PYTHON_VER" "$GREEN"

# Create virtual environment
if [[ ! -d "$VENV_DIR" ]]; then
    print_message "Creating virtual environment..." "$GREEN"
    python3 -m venv "$VENV_DIR" || handle_error "Failed to create virtual environment"
else
    print_message "Virtual environment already exists." "$YELLOW"
fi

# Activate virtual environment
print_message "Activating virtual environment..." "$GREEN"
if [[ "$OS_TYPE" == "windows" ]]; then
    source "$VENV_DIR/Scripts/activate" || handle_error "Failed to activate virtual environment"
else
    source "$VENV_DIR/bin/activate" || handle_error "Failed to activate virtual environment"
fi

# Upgrade pip
print_message "Upgrading pip..." "$GREEN"
pip install --upgrade pip || handle_error "Failed to upgrade pip"

# Install requirements
if [[ -f "$REQUIREMENTS_FILE" ]]; then
    print_message "Installing requirements..." "$GREEN"
    pip install -r "$REQUIREMENTS_FILE" || handle_error "Failed to install requirements"
else
    print_message "No requirements.txt found. Skipping package installation." "$YELLOW"
fi

# Create necessary directories
print_message "Creating project directories..." "$GREEN"
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/config"

# Create .env file if it doesn't exist
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
    print_message "Creating .env file..." "$GREEN"
    cat > "$PROJECT_DIR/.env" << EOF
# Environment variables for $PROJECT_NAME
DEBUG=True
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///$PROJECT_DIR/data/database.db
EOF
fi

# Set up pre-commit hooks if .pre-commit-config.yaml exists
if [[ -f "$PROJECT_DIR/.pre-commit-config.yaml" ]]; then
    print_message "Setting up pre-commit hooks..." "$GREEN"
    if command_exists pre-commit; then
        pre-commit install || print_message "Failed to install pre-commit hooks" "$YELLOW"
    else
        print_message "pre-commit not installed. Skipping hook setup." "$YELLOW"
    fi
fi

# Make scripts executable
print_message "Making scripts executable..." "$GREEN"
find "$PROJECT_DIR/scripts" -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true

print_message "=========================================" "$GREEN"
print_message "Setup completed successfully!" "$GREEN"
print_message "To activate the virtual environment:" "$GREEN"
if [[ "$OS_TYPE" == "windows" ]]; then
    print_message "  source $VENV_DIR/Scripts/activate" "$GREEN"
else
    print_message "  source $VENV_DIR/bin/activate" "$GREEN"
fi
print_message "=========================================" "$GREEN"