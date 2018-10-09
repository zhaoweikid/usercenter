#!/bin/bash
python3 server.py debug $1
#watchmedo auto-restart -d . -p "*.py" python server.py debug $1
