#!/bin/bash

# Nine Men's Morris Launcher Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Nine Men's Morris - Strategic Board Game${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import pygame" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Launch the game
echo -e "${GREEN}✓ Launching game...${NC}"
echo ""
python main.py "$@"

# Deactivate when done
deactivate

