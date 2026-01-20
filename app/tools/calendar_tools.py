"""
Calendar Tools for AI Agent

Функции для работы с Google Calendar через AI агента.
"""

from datetime import datetime, timedelta
from typing import Annotated
from app.services.google_calendar import GoogleCalendarService
import re


def parse_russian_date(date_str: str) -> datetime:
    """
    Парсит русскоязычные описания дат в datetime.

    Args:
        date_str: Строка с датой ("завтра", "в пятницу", "через неделю", "2025-01-20 15:00")

    Returns:
        datetime объект
    """
    date_str = date_str.lower().strip()
    now = datetime.now()

    # ISO формат с временем
    if re.match(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", date_str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")

    # ISO формат без времени (берём 10:00 по умолчанию)
    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        return datetime.strptime(date_str + " 10:00", "%Y-%m-%d %H:%M")

    # Относительные даты
    if "завтра" in date_str:
        base = now + timedelta(days=1)
    elif "послезавтра" in date_str:
        base = now + timedelta(days=2)
    elif "сегодня" in date_str:
        base = now
    elif "через неделю" in date_str:
        base = now + timedelta(weeks=1)
    elif "через месяц" in date_str:
        base = now + timedelta(days=30)
    else:
        # По умолчанию - завтра
        base = now + timedelta(days=1)

    # Извлекаем время если указано
    time_match = re.search(r"(\d{1,2}):(\d{2})", date_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        return base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        # Время по умолчанию 10:00
        return base.replace(hour=10, minute=0, second=0, microsecond=0)


async def create_calendar_event(
    title: Annotated[str, "Название события"],
    start_date: Annotated[str, "Дата и время начала (например: 'завтра в 15:00', '2025-01-20 10:00')"],
    duration_minutes: Annotated[int, "Длительность в минутах"] = 60,
    description: Annotated[str | None, "Описание события"] = None,
    location: Annotated[str | None, "Место проведения"] = None,
    calendar: GoogleCalendarService | None = None
) -> str:
    """
    Создаёт событие в Google Calendar.
    Используй для встреч, звонков, напоминаний с конкретным временем.

    Args:
        title: Название события
        start_date: Дата/время начала
        duration_minutes: Длительность в минутах (по умолчанию 60)
        description: Описание события
        location: Место проведения
        calendar: GoogleCalendarService instance (передаётся автоматически)

    Returns:
        Сообщение об успешном создании события
    """
    if calendar is None:
        raise ValueError("GoogleCalendarService не передан!")

    try:
        # Парсим дату начала
        start_datetime = parse_russian_date(start_date)

        # Вычисляем дату окончания
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)

        # Создаём событие (синхронный вызов Google API)
        calendar.create_event(
            summary=title,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            location=location
        )

        return (
            f"Событие '{title}' создано в календаре на "
            f"{start_datetime.strftime('%d.%m.%Y %H:%M')} "
            f"(длительность: {duration_minutes} мин)"
        )

    except Exception as e:
        return f"Ошибка создания события: {str(e)}"


async def list_calendar_events(
    max_results: Annotated[int, "Максимальное количество событий"] = 5,
    calendar: GoogleCalendarService | None = None
) -> str:
    """
    Возвращает список ближайших событий в календаре.
    Используй когда пользователь спрашивает "что у меня в календаре", "какие встречи на неделе".

    Args:
        max_results: Сколько событий показать (по умолчанию 5)
        calendar: GoogleCalendarService instance

    Returns:
        Список событий в виде строки
    """
    if calendar is None:
        raise ValueError("GoogleCalendarService не передан!")

    try:
        events = calendar.list_upcoming_events(max_results=max_results)

        if not events:
            return "В календаре нет ближайших событий."

        result = f"Ближайшие события ({len(events)}):\n\n"
        for i, event in enumerate(events, 1):
            start = event["start"]
            # Парсим дату
            try:
                dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%d.%m.%Y %H:%M')
            except (ValueError, AttributeError):
                formatted_date = start

            result += f"{i}. {event['summary']} - {formatted_date}\n"

        return result

    except Exception as e:
        return f"Ошибка получения событий: {str(e)}"
