from apify_client import ApifyClient
from config import APIFY_TOKEN

async def check_fake_subscribers(username: str) -> dict:
    try:
        client = ApifyClient(APIFY_TOKEN)
        run = client.actor("s_actors/telegram-channel-analytics").call(
            run_input={"analyze": [f"@{username}"], "postsToAnalyze": 100}
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        if not items:
            return {"error": "Apify: пустой ответ"}
        r = items[0]
        return {
            "quality_score": r.get("qualityLevel", 0),
            "warnings": r.get("warnings", []),
            "err_percent": r.get("errPercent"),
            "error": None,
        }
    except Exception as exc:
        return {"error": f"Apify: {exc}"}
