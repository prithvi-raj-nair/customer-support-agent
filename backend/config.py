import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Model settings
MAIN_MODEL = "claude-sonnet-4-20250514"
GUARDRAIL_MODEL = "claude-3-5-haiku-20241022"

# Company context
COMPANY_NAME = "Shamazon"
COMPANY_DESCRIPTION = "An e-commerce platform specializing in fast delivery and excellent customer service"
