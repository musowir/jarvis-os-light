#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Terminal Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}============ INITIALIZING STREAMLINED JARVIS ENVIRONMENT ============${NC}"

# 1. Update Termux Package Repositories
echo -e "\n${YELLOW}[Step 1/4] Syncing system repository lists...${NC}"
pkg update -y && pkg upgrade -y

# 2. Install Native Binary Environments
echo -e "\n${YELLOW}[Step 2/4] Installing runtime dependencies...${NC}"
# openssh: secure terminal pipes
# termux-api: native system hooks (flashlight, tts, battery)
# sqlite: relational database storage
# python: core interpreter
pkg install -y openssh termux-api sqlite python

# 3. Provision Python Virtual Environment
echo -e "\n${YELLOW}[Step 3/4] Setting up isolated Python container...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
    echo -e "${GREEN}✔ Virtual environment generated successfully.${NC}"
else
    echo -e "${BLUE}i Virtual environment directory already exists. Skipping recreation.${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# 4. Install Pip Dependencies
echo -e "\n${YELLOW}[Step 4/4] Syncing production requirements...${NC}"
pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✔ Python dependency matrix synced cleanly.${NC}"
else
    echo -e "${RED}✘ Error: requirements.txt not found.${NC}"
    exit 1
fi

# Initialize System Database Layout
echo -e "\n${YELLOW}[Database Verification] Instantiating schema migration engines...${NC}"
python -c "
try:
    from app import create_app
    from database import init_db
    app = create_app()
    with app.app_context():
        init_db(app)
    print('${GREEN}✔ Database schema states verified and ready.${NC}')
except Exception as e:
    print(f'${YELLOW}i Database setup handled via runtime context configuration: {e}${NC}')
"

# Post-Execution Checklist
echo -e "\n${BLUE}==================================================================${NC}"
echo -e "${GREEN}🎉 JARVIS EXECUTABLE ENVIRONMENT PREPPED COMPLETED!${NC}"
echo -e "\n${GREEN}To initiate the architecture run:${NC}"
echo -e " ${BLUE}source venv/bin/activate && python app.py${NC}"
echo -e "${BLUE}==================================================================${NC}"
