from tgstat import TGStatClient
from tgstat.exceptions import TGStatError
from config import TGSTAT_TOKEN

async def get_channel_stat(username: str) -> dict:
    try:
        async with TGStatClient(token=TGSTAT_TOKEN) as client:
            channel = await client.channels.get(channel_id=f"@{username}")
            stat = await client.channels.stat(channel_id=f"@{username}")
            return {
                "title": channel.title,
                "participants": stat.participants_count,
                "avg_post_reach": stat.avg_post_reach,
                "error": None,
            }
    except TGStatError as exc:
        return {"error": f"TGStat: {exc.__class__.__name__}: {exc}"}
    except Exception as exc:
        return {"error": f"TGStat: {exc}"}
