import re
from typing import Optional

_PATTERN = re.compile(r"(?:https?://)?(?:t\.me/)?@?([a-zA-Z0-9_]{5,32})")

def extract_username(text: str) -> Optional[str]:
    match = _PATTERN.search(text.strip())
    return match.group(1) if match else None
