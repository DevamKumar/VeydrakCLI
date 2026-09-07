import os
from dotenv import load_dotenv

# Load environment variables automatically
load_dotenv()

# We can place global configuration variables here in the future
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
FAST_MODEL = os.getenv("FAST_MODEL", "gpt-4o-mini")
