"""
Google Calendar Service

Сервис для работы с Google Calendar API.
Использует Service Account для серверной авторизации.
"""

from datetime import datetime, timedelta
from typing import Optional
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """
    Сервис для работы с Google Calendar.

    Использует Service Account credentials для авторизации.
    """

    def __init__(self, credentials_json: dict, calendar_id: str = "primary"):
        """
        Инициализация сервиса.

        Args:
            credentials_json: Service Account credentials в формате dict
            calendar_id: ID календаря (default: "primary")
        """
        self.calendar_id = calendar_id

        # Создаём credentials из JSON
        credentials = service_account.Credentials.from_service_account_info(
            credentials_json,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )

        # Создаём клиент Calendar API
        self.service = build("calendar", "v3", credentials=credentials)

    async def create_event(
        self,
        summary: str,
        start_datetime: datetime,
        end_datetime: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> dict:
        """
        Создаёт событие в календаре.

        Args:
            summary: Название события
            start_datetime: Дата и время начала
            end_datetime: Дата и время окончания (по умолчанию +1 час)
            description: Описание события
            location: Место проведения

        Returns:
            dict с информацией о созданном событии

        Raises:
            Exception: Если создание события не удалось
        """
        try:
            # Если end_datetime не указан, берём +1 час от начала
            if end_datetime is None:
                end_datetime = start_datetime + timedelta(hours=1)

            # Формируем событие
            event = {
                "summary": summary,
                "start": {
                    "dateTime": start_datetime.isoformat(),
                    "timeZone": "Europe/Moscow",  # Можно сделать настраиваемым
                },
                "end": {
                    "dateTime": end_datetime.isoformat(),
                    "timeZone": "Europe/Moscow",
                },
            }

            # Добавляем опциональные поля
            if description:
                event["description"] = description
            if location:
                event["location"] = location

            # Создаём событие
            result = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()

            logger.info(f"Created calendar event: {summary} at {start_datetime}")

            return {
                "id": result.get("id"),
                "summary": result.get("summary"),
                "start": result["start"].get("dateTime"),
                "end": result["end"].get("dateTime"),
                "htmlLink": result.get("htmlLink")
            }

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}", exc_info=True)
            raise Exception(f"Ошибка создания события: {e}")
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}", exc_info=True)
            raise

    async def list_upcoming_events(self, max_results: int = 10) -> list[dict]:
        """
        Получает список ближайших событий.

        Args:
            max_results: Максимальное количество событий

        Returns:
            Список событий
        """
        try:
            now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])

            return [
                {
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "start": event["start"].get("dateTime", event["start"].get("date")),
                    "end": event["end"].get("dateTime", event["end"].get("date")),
                }
                for event in events
            ]

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}", exc_info=True)
            raise Exception(f"Ошибка получения событий: {e}")
        except Exception as e:
            logger.error(f"Error listing events: {e}", exc_info=True)
            raise
