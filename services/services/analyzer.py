def analyze_channel_quality(participants: int, avg_reach: int, err_percent: float | None) -> dict:
    """
    Бесплатная эвристика для оценки качества канала.
    Возвращает словарь с оценкой (0-100), предупреждениями и вердиктом.
    """
    score = 100
    warnings = []

    # 1. Проверка на минимальное количество подписчиков
    if participants < 1000:
        warnings.append("Слишком мало подписчиков (менее 1000). Высокий риск слива бюджета.")
        score -= 30

    # 2. Проверка соотношения охвата к подписчикам (Reach / Subs)
    if participants > 0:
        reach_ratio = (avg_reach / participants) * 100
        if reach_ratio < 10:
            warnings.append(f"Крайне низкий охват: всего {reach_ratio:.1f}% от подписчиков видят посты. Признак мертвых душ.")
            score -= 40
        elif reach_ratio < 20:
            warnings.append(f"Низкий охват: {reach_ratio:.1f}%. Возможно, часть аудитории неактивна.")
            score -= 15
        elif reach_ratio > 80:
            warnings.append(f"Аномально высокий охват ({reach_ratio:.1f}%). Возможна накрутка просмотров.")
            score -= 20

    # 3. Проверка ERR (Engagement Rate by Reach)
    if err_percent is not None:
        if err_percent < 3:
            warnings.append(f"Очень низкая вовлеченность (ERR {err_percent:.1f}%). Люди не читают канал.")
            score -= 30
        elif err_percent > 60:
            warnings.append(f"Подозрительно высокая вовлеченность (ERR {err_percent:.1f}%). Возможно, используются боты для реакций.")
            score -= 20

    # Ограничиваем оценку снизу нулем
    score = max(0, score)

    # Формируем вердикт
    if score >= 70 and not warnings:
        verdict = "✅ ЧИСТО. Можно покупать рекламу."
    elif score >= 40:
        verdict = "⚠️ ЕСТЬ СОМНЕНИЯ. Рекомендую проверить вручную."
    else:
        verdict = "❌ НАКРУТКА. Покупку рекламы лучше отменить."

    return {
        "score": score,
        "warnings": warnings,
        "verdict": verdict,
        "err_percent": err_percent
    }
