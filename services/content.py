from tgstat import TGStatClient
from config import TGSTAT_TOKEN, CRYPTO_THRESHOLD

CRYPTO_KEYWORDS = {
    "bitcoin", "btc", "ethereum", "eth", "defi", "nft", "web3",
    "blockchain", "блокчейн", "криптовалюта", "токен", "альткоин",
    "altcoin", "binance", "solana", "toncoin", "ton", "crypto", "крипта",
}

async def is_crypto_channel(username: str, min_posts: int = 20) -> tuple[bool, float]:
    try:
        async with TGStatClient(token=TGSTAT_TOKEN) as client:
            posts = await client.channels.posts(channel_id=f"@{username}", limit=min_posts)
            if not posts.items:
                return False, 0.0
            matches = sum(
                1 for post in posts.items
                if any(kw in (post.text or "").lower() for kw in CRYPTO_KEYWORDS)
            )
            ratio = matches / len(posts.items)
            return ratio >= CRYPTO_THRESHOLD, ratio
    except Exception:
        return False, 0.0
