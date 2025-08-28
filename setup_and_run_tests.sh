#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up environment for serverless_mcp tests...${NC}"

# Define environment variables
VENV_DIR="venv"
CURRENT_DIR=$(pwd)
PARENT_DIR=$(dirname $CURRENT_DIR)

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv $VENV_DIR
else
    echo -e "${YELLOW}Using existing virtual environment...${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -e .  # Install the package in editable/development mode

# Fix test imports by modifying the test file to use relative imports
echo -e "${YELLOW}Fixing test imports...${NC}"
test_file="tests/test_tool_integration.py"
# Make a backup of the original file
cp $test_file ${test_file}.bak

# Modify the import to use relative import
sed -i.sedtmp 's/from serverless_mcp\.loader/from loader/g' $test_file
sed -i.sedtmp 's/from serverless_mcp\.serverless_mcp_tools/from serverless_mcp_tools/g' $test_file

rm -f ${test_file}.sedtmp

# Fix the test discovery
echo -e "${YELLOW}Creating temporary test runner...${NC}"
cat > run_tests.py << EOL
import unittest
import sys
import os

# Add the current directory to the path so we can import modules directly
sys.path.insert(0, os.path.abspath('.'))

if __name__ == '__main__':
    # Run all tests in the tests directory
    test_suite = unittest.defaultTestLoader.discover('tests')
    result = unittest.TextTestRunner().run(test_suite)
    sys.exit(not result.wasSuccessful())
EOL

# Run tests with proper path setup
echo -e "${GREEN}Running tests...${NC}"
python run_tests.py

# Clean up
echo -e "${YELLOW}Cleaning up...${NC}"
rm -f run_tests.py
mv ${test_file}.bak $test_file

# Deactivate virtual environment
deactivate

echo -e "${GREEN}Tests completed.${NC}" 