from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from utils.validators import extract_username
from services.tgstat import get_channel_stat
from services.apify import check_fake_subscribers
from services.content import is_crypto_channel
from database.storage import save_audit, get_previous_audit, get_history

router = Router()

class IsOwner(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == OWNER_ID

class IsOwnerCallback(Filter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.from_user.id == OWNER_ID

def _fmt(value) -> str:
    return f"{value:,}".replace(",", " ") if value else "—"

def _format_delta(prev: dict, current_score: int) -> str:
    if not prev or prev.get("quality_score") is None:
        return ""
    diff = current_score - prev["quality_score"]
    if diff == 0:
        return "\n<i>📈 Оценка не изменилась.</i>"
    arrow = "📈" if diff > 0 else "📉"
    sign = "+" if diff > 0 else ""
    prev_date = datetime.fromisoformat(prev["created_at"]).strftime("%d.%m.%Y")
    return f"\n<i>{arrow} С прошлой проверки ({prev_date}): {sign}{diff} баллов</i>"

def _verdict(score: int, warnings: list[str]) -> str:
    if score >= 70 and not warnings:
        return "✅ ЧИСТО. Можно покупать рекламу."
    if score >= 40:
        return "⚠️ ЕСТЬ СОМНЕНИЯ. Рекомендую проверить вручную."
    return "❌ НАКРУТКА. Покупку рекламы лучше отменить."

def _build_keyboard(username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Повторить проверку", callback_data=f"retry:{username}"),
        InlineKeyboardButton(text="📜 История", callback_data=f"history:{username}"),
    ]])

async def run_audit(username: str) -> tuple[str, dict | None]:
    stat = await get_channel_stat(username)
    if stat.get("error"):
        return f"❌ {stat['error']}", None
    is_crypto, ratio = await is_crypto_channel(username)
    if not is_crypto:
        return f"⚠️ Канал @{username} не похож на крипто-тематический (крипто-постов: {ratio:.0%}).", None
    fake = await check_fake_subscribers(username)
    if fake.get("error"):
        return f"❌ {fake['error']}", None
    score = int(fake.get("quality_score") or 0)
    warnings = fake.get("warnings") or []
    err = fake.get("err_percent")
    verdict = _verdict(score, warnings)
    prev = get_previous_audit(username)
    delta_text = _format_delta(prev, score)
    warnings_text = "\n".join(f"• {w}" for w in warnings) if warnings else "Нет"
    err_text = f"{err:.2f}%" if isinstance(err, (int, float)) else "—"
    text = (
        f"<b>📊 Аудит канала @{username}</b>\n\n"
        f"<b>Название:</b> {stat['title']}\n"
        f"<b>Подписчиков:</b> {_fmt(stat['participants'])}\n"
        f"<b>Средний охват:</b> {_fmt(stat['avg_post_reach'])}\n"
        f"<b>ERR:</b> {err_text}\n"
        f"<b>Крипто-контент:</b> {ratio:.0%} постов\n\n"
        f"<b>Оценка качества (Apify):</b> {score}/100{delta_text}\n\n"
        f"<b>Предупреждения:</b>\n{warnings_text}\n\n"
        f"<b>Вердикт:</b> {verdict}"
    )
    payload = {
        "username": username, "title": stat["title"],
        "participants": stat["participants"], "avg_reach": stat["avg_post_reach"],
        "quality_score": score, "err_percent": err if isinstance(err, (int, float)) else None,
        "warnings": warnings, "verdict": verdict,
    }
    return text, payload

@router.message(IsOwner(), F.text)
async def handle_link(message: Message):
    username = extract_username(message.text)
    if not username:
        await message.answer("Не удалось распознать ссылку. Пришли @username или t.me/username.")
        return
    status = await message.answer(f"🔍 Анализирую @{username}…")
    text, payload = await run_audit(username)
    if payload is None:
        await status.edit_text(text, parse_mode="HTML")
        return
    save_audit(payload)
    await status.edit_text(text, parse_mode="HTML", reply_markup=_build_keyboard(username))

@router.callback_query(IsOwnerCallback(), F.data.startswith("retry:"))
async def handle_retry(callback: CallbackQuery):
    username = callback.data.split(":", 1)[1]
    await callback.answer("Запускаю повторную проверку…")
    try:
        await callback.message.edit_text(f"🔍 Анализирую @{username}…")
    except Exception:
        pass
    text, payload = await run_audit(username)
    if payload is None:
        await callback.message.edit_text(text, parse_mode="HTML")
        return
    save_audit(payload)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=_build_keyboard(username))

@router.callback_query(IsOwnerCallback(), F.data.startswith("history:"))
async def handle_history(callback: CallbackQuery):
    username = callback.data.split(":", 1)[1]
    history = get_history(username, limit=5)
    await callback.answer()
    if not history:
        await callback.message.answer(f"📜 История для @{username} пуста.")
        return
    lines = [f"<b>📜 Последние проверки @{username}</b>\n"]
    for item in history:
        date = datetime.fromisoformat(item["created_at"]).strftime("%d.%m.%Y %H:%M")
        score = item["quality_score"] or 0
        verdict_short = "✅" if score >= 70 else ("⚠️" if score >= 40 else "❌")
        lines.append(f"{verdict_short} <b>{date}</b> — {score}/100 (ERR: {item['err_percent'] or '—'})")
    if len(history) >= 2:
        newest, oldest = history[0]["quality_score"] or 0, history[-1]["quality_score"] or 0
        diff = newest - oldest
        sign = "+" if diff > 0 else ""
        lines.append(f"\n<i>Изменение за период: {sign}{diff} баллов</i>")
    await callback.message.answer("\n".join(lines), parse_mode="HTML")
