import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
TGSTAT_TOKEN: str = os.getenv("TGSTAT_TOKEN", "")
APIFY_TOKEN: str = os.getenv("APIFY_TOKEN", "")
CRYPTO_THRESHOLD: float = float(os.getenv("CRYPTO_THRESHOLD", "0.30"))
