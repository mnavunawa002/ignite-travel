# Load the environment variables
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(
  Path(__file__).parent.parent / ".env"
)


