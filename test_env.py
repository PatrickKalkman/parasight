# test_env.py
import os
import pathlib

from dotenv import load_dotenv

# Get the absolute path to the current directory
current_dir = pathlib.Path(__file__).parent.absolute()
# Explicitly point to the .env file
env_path = current_dir / ".env"

print(f"Looking for .env at: {env_path}")
print(f"File exists: {env_path.exists()}")

# Try to load with explicit path
load_dotenv(dotenv_path=env_path)

# Check if it's loaded
api_key = os.environ.get("OPENAI_API_KEY", "Not found")
print(f"OPENAI_API_KEY: {api_key}")
