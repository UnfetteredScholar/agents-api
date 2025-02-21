#!/bin/bash

mkdir -p "app/api/v1/routers"
mkdir -p "app/core"
mkdir -p "app/schemas"
mkdir -p "app/logs"
mkdir -p "app/tests"

touch "app/main.py"
touch "app/core/config.py"
touch "Dockerfile"
touch "compose.yaml"
touch ".env"
touch ".env.example"
touch ".gitignore"
touch "README.md"

echo -e ".env\nlogs\n.venv\n__pycache__" > .gitignore