import os
import logging
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_TIMEOUT = 30

load_dotenv()

# Check if spaCy is available for neural embeddings
USE_EMBEDDINGS = False
try:
    import spacy
    USE_EMBEDDINGS = True
    print("spaCy available - using neural embedding-based search")
except ImportError:
    print("spaCy not available - using keyword-based search")

@dataclass
class Settings:
    openai_api_key: str
    openai_model: str = DEFAULT_OPENAI_MODEL
    openai_timeout: int = DEFAULT_OPENAI_TIMEOUT
    
    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        return cls(
            openai_api_key=api_key,
            openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            openai_timeout=int(os.getenv("OPENAI_TIMEOUT", DEFAULT_OPENAI_TIMEOUT))
        )

class Paths:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    ORDERS_FILE = DATA_DIR / "orders.json"
    PRODUCTS_FILE = DATA_DIR / "products.json"

def setup_logging():
    """Setup logging to console only - no log files."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
