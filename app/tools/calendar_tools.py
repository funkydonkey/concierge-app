"""
Calendar Tools for AI Agent

Функции для работы с Google Calendar через AI агента.
"""

from datetime import datetime, timedelta
from typing import Annotated
from app.services.google_calendar import GoogleCalendarService
import re
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)


def parse_russian_date(date_str: str, timezone: str = "Europe/Berlin") -> datetime:
    """
    Парсит русскоязычные описания дат в datetime с учетом временной зоны.

    Args:
        date_str: Строка с датой ("завтра", "в пятницу", "через неделю", "2026-01-20 15:00")
        timezone: Временная зона (по умолчанию Europe/Berlin)

    Returns:
        datetime объект с временной зоной
    """
    date_str = date_str.lower().strip()
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)

    logger.info(f"📅 Parsing date: '{date_str}' (current time: {now.strftime('%Y-%m-%d %H:%M %Z')})")

    # ISO формат с временем
    if re.match(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=tz)

    # ISO формат без времени (берём 10:00 по умолчанию)
    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        dt = datetime.strptime(date_str + " 10:00", "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=tz)

    # Парсим даты типа "3 февраля", "15 марта" и т.д.
    months_ru = {
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
        "мая": 5, "июня": 6, "июля": 7, "августа": 8,
        "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12
    }

    # Ищем паттерн: число + месяц (например "3 февраля")
    date_pattern = re.search(r"(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)", date_str)
    if date_pattern:
        day = int(date_pattern.group(1))
        month = months_ru[date_pattern.group(2)]
        logger.info(f"   ✓ Matched Russian date: day={day}, month={month}")

        # Определяем год: если дата уже прошла в текущем году, берём следующий год
        year = now.year
        try:
            target_date = now.replace(year=year, month=month, day=day)
            if target_date < now:
                # Дата уже прошла в этом году, берём следующий год
                logger.info(f"   → Date {target_date.date()} is in the past, using next year")
                year = now.year + 1
                target_date = now.replace(year=year, month=month, day=day)
            logger.info(f"   → Calculated date: {target_date.strftime('%Y-%m-%d')}")
        except ValueError:
            # Невалидная дата (например 31 февраля)
            logger.warning(f"   ✗ Invalid date: {day}/{month}, using tomorrow")
            target_date = now + timedelta(days=1)

        # Извлекаем время если указано
        time_match = re.search(r"(\d{1,2}):(\d{2})", date_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            result = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            result = target_date.replace(hour=10, minute=0, second=0, microsecond=0)

        logger.info(f"   ✅ Final parsed date: {result.strftime('%Y-%m-%d %H:%M %Z')}")
        return result

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
        return "❌ Ошибка: Google Calendar не настроен. Добавьте GOOGLE_CALENDAR_CREDENTIALS_JSON в переменные окружения."

    try:
        # Парсим дату начала с учетом timezone календаря
        start_datetime = parse_russian_date(start_date, timezone=calendar.timezone)

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
        return "❌ Ошибка: Google Calendar не настроен. Добавьте GOOGLE_CALENDAR_CREDENTIALS_JSON в переменные окружения."

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
