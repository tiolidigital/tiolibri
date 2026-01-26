#!/bin/bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib"
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
