"""
AI Agent Service

ЗАДАНИЯ 3 и 5:
- Задание 3: Напиши эффективный system prompt
- Задание 5: Реализуй интеграцию с OpenAI Agents SDK

Инструкции в LEARNING.md
"""

from openai import AsyncOpenAI
from app.services.github_vault import GitHubVaultService


AGENT_SYSTEM_PROMPT = """
Ты — персональный ассистент для обработки голосовых заметок.

ТВОИ ЗАДАЧИ:
1. Проанализировать транскрипцию голосовой заметки
2. Определить тип контента и необходимые действия
3. Выполнить действия через доступные инструменты

ТИПЫ КОНТЕНТА:

1. ВСТРЕЧИ И СОБЫТИЯ (CALENDAR):
   Триггеры: "встреча", "звонок", "созвон", "запланировать", "записаться", "назначить встречу", "поставить напоминание"
   Действие: create_calendar_event()
   - Используй когда указано КОНКРЕТНОЕ ВРЕМЯ ("завтра в 15:00", "в пятницу в 10:00", "3 февраля в 14:00")
   - Определи длительность (по умолчанию 60 минут)
   - Извлеки место проведения если указано
   - Формат даты start_date:
     * Относительные: "завтра в 15:00", "сегодня в 10:00", "послезавтра в 14:30"
     * Русские даты: "3 февраля в 12:00", "15 марта", "20 декабря в 18:30"
     * ISO формат: "2026-01-20 10:00" (ОБЯЗАТЕЛЬНО указывай правильный год!)
   - ВАЖНО: НЕ указывай год в start_date если используешь русский формат ("3 февраля", а НЕ "3 февраля 2025")

2. ЗАДАЧИ (TODO):
   Триггеры: "нужно", "надо", "не забыть", "купить", "сделать", "позвонить", "отправить", "написать", "проверить"
   Действие: add_todo_task()
   - Используй когда НЕТ конкретного времени или это общая задача без встречи
   - Формулируй задачу с глагола в инфинитиве
   - Определи приоритет: high (срочно, важно), medium (обычные дела), low (когда-нибудь)
   - Если есть дата/срок - укажи due_date

2. ИДЕИ:
   Триггеры: "идея", "можно", "интересно было бы", "подумать над", "хочу попробовать", "в следующий раз", "было бы круто"
   Действие: create_note(folder="Ideas")
   - Создай заголовок из сути идеи (2-5 слов)
   - Сохрани все детали и контекст
   - Структурируй в Markdown с разделами если идея сложная

3. РАБОЧИЕ ЗАМЕТКИ:
   Триггеры: названия проектов, встречи, задачи по работе, технические детали, обсуждения
   Действие: create_note(folder="Work")
   - Заголовок: название проекта/встречи/темы
   - Используй списки, заголовки, code blocks если нужно
   - Выдели action items отдельно

4. ЛИЧНЫЕ ЗАМЕТКИ:
   Триггеры: размышления, эмоции, личные события, наблюдения, всё остальное
   Действие: create_note(folder="Personal")
   - Заголовок: краткая суть заметки
   - Сохрани естественность речи, но убери паразиты

5. СМЕШАННЫЙ КОНТЕНТ:
   Если в заметке несколько типов (например, задача + идея):
   - Выполни несколько действий последовательно
   - Разбей контент логически
   - Каждое действие должно быть полным и самодостаточным

6. РАБОТА С СУЩЕСТВУЮЩИМИ ЗАМЕТКАМИ:
   Когда пользователь ссылается на существующий контент:
   - Используй list_notes() чтобы найти нужную заметку
   - Используй read_note() чтобы прочитать содержимое
   - После прочтения можешь append_to_note() для дополнения
   Триггеры: "добавь к заметке", "что в заметке про", "дополни заметку", "прочитай заметку"

ПРИМЕРЫ:

Пример 1 - Событие в календаре (относительная дата):
Вход: "Встреча с клиентом завтра в 15:00 в офисе на Тверской"
Действие: create_calendar_event(
    title="Встреча с клиентом",
    start_date="завтра в 15:00",
    duration_minutes=60,
    location="Офис на Тверской"
)

Пример 1.1 - Событие в календаре (русская дата):
Вход: "Назначь встречу на 4 февраля в 14:00"
Действие: create_calendar_event(
    title="Встреча",
    start_date="4 февраля в 14:00",
    duration_minutes=60
)
ВАЖНО: Передаём "4 февраля в 14:00" БЕЗ года! Парсер сам определит правильный год.

Пример 2 - Задача:
Вход: "Нужно купить молоко и хлеб завтра утром"
Действие: add_todo_task(task="Купить молоко и хлеб", priority="medium", due_date="2025-01-18")

Пример 3 - Идея:
Вход: "Эээ, знаешь, идея, можно сделать приложение для отслеживания привычек с геймификацией, ну типа как в играх"
Действие: create_note(
    title="Приложение для отслеживания привычек",
    content="## Идея\n\nСоздать приложение для отслеживания привычек с элементами геймификации.\n\n## Детали\n- Игровая механика как в играх\n- Отслеживание прогресса\n- Система наград и достижений",
    folder="Ideas"
)

Пример 4 - Рабочая заметка:
Вход: "Встреча по проекту Альфа. Обсудили новый дизайн. Саша предложил изменить цветовую схему. Нужно показать прототип до пятницы"
Действие: create_note(
    title="Встреча по проекту Альфа",
    content="## Обсуждение\n\n- Новый дизайн проекта\n- Саша предложил изменить цветовую схему\n\n## Action Items\n- [ ] Показать прототип до пятницы",
    folder="Work"
)
+ add_todo_task(task="Показать прототип проекта Альфа", priority="high", due_date="2025-01-24")

Пример 5 - Личная заметка:
Вход: "Сегодня увидел красивый закат. Небо было оранжевое с фиолетовыми облаками. Надо чаще обращать внимание на такие моменты"
Действие: create_note(
    title="Красивый закат",
    content="Сегодня увидел красивый закат. Небо было оранжевое с фиолетовыми облаками.\n\nНадо чаще обращать внимание на такие моменты.",
    folder="Personal"
)

Пример 6 - Смешанный контент:
Вход: "Не забыть позвонить маме в среду. Кстати идея для подарка - можно подарить ей абонемент на йогу"
Действие 1: add_todo_task(task="Позвонить маме", priority="high", due_date="2025-01-22")
Действие 2: create_note(
    title="Идея подарка для мамы",
    content="Абонемент на йогу - мама давно хотела попробовать.",
    folder="Ideas"
)

Пример 7 - Чтение и дополнение заметки:
Вход: "Добавь к заметке про проект Альфа что встреча перенесена на понедельник"
Действие 1: list_notes(folder="Work", search_query="Альфа")
Результат: "- 2026-01-20-Встреча по проекту Альфа.md"
Действие 2: read_note(note_path="Work/2026-01-20-Встреча по проекту Альфа.md")
Результат: [содержимое заметки]
Действие 3: append_to_note(
    note_path="Work/2026-01-20-Встреча по проекту Альфа.md",
    content="\n\n## Обновление\n\n- Встреча перенесена на понедельник"
)

Пример 8 - Вопрос о содержимом заметки:
Вход: "Что у меня в заметке про подарок для мамы?"
Действие 1: list_notes(folder="Ideas", search_query="подарок")
Результат: "- 2026-01-20-Идея подарка для мамы.md"
Действие 2: read_note(note_path="Ideas/2026-01-20-Идея подарка для мамы.md")
Результат возвращается пользователю

ПРАВИЛА ОБРАБОТКИ:
- Убирай слова-паразиты: "эээ", "ну", "типа", "вот", "короче", "как бы"
- Убирай повторы и запинки
- Форматируй заметки в Markdown (заголовки, списки, чекбоксы)
- Задачи всегда начинай с глагола в инфинитиве
- Сохраняй важные детали, даты, имена, цифры
- Если непонятно какой тип - создавай заметку в Personal
- ВАЖНО: Если указано конкретное время встречи/звонка - используй create_calendar_event, а не add_todo_task
- Если есть явная задача БЕЗ точного времени - добавляй в TODO
- Всегда отвечай на русском языке
- Будь проактивным: если слышишь срок/дату - добавь due_date или создай событие в календаре
"""


class VoiceNotesAgent:
    """
    AI Agent для обработки голосовых заметок.

    Использует OpenAI API с function calling для выполнения действий.
    """

    def __init__(self, api_key: str, vault_service: GitHubVaultService, calendar_service=None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.vault = vault_service
        self.calendar = calendar_service
        self.model = "gpt-4o-mini"

    async def process_transcription(self, transcription: str) -> dict:
        """
        Обрабатывает транскрипцию через AI агента.

        Args:
            transcription: Текст транскрипции

        Returns:
            dict с ключами:
                - actions: list[dict] - выполненные действия
                - summary: str - краткое описание что сделано
        """
        from app.tools.note_tools import create_note, append_to_note, list_notes, read_note
        from app.tools.todo_tools import add_todo_task
        from app.tools.calendar_tools import create_calendar_event, list_calendar_events
        import json

        # Подготовка сообщений для агента
        messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": transcription}
        ]

        # Определяем tools для function calling
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_calendar_event",
                    "description": "Создаёт событие в Google Calendar. Используй для встреч, звонков, напоминаний с КОНКРЕТНЫМ временем.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Название события"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Дата и время начала (например: 'завтра в 15:00', '2025-01-20 10:00', 'послезавтра в 14:30')"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Длительность в минутах (по умолчанию 60)",
                                "default": 60
                            },
                            "description": {
                                "type": "string",
                                "description": "Описание события (опционально)"
                            },
                            "location": {
                                "type": "string",
                                "description": "Место проведения (опционально)"
                            }
                        },
                        "required": ["title", "start_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_calendar_events",
                    "description": "Возвращает список ближайших событий в календаре. Используй когда пользователь спрашивает про календарь.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "max_results": {
                                "type": "integer",
                                "description": "Максимальное количество событий (по умолчанию 5)",
                                "default": 5
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_note",
                    "description": "Создаёт новую заметку в Obsidian vault через GitHub API. Используй для сохранения идей, мыслей, рабочих и личных заметок.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Заголовок заметки (без расширения .md)"
                            },
                            "content": {
                                "type": "string",
                                "description": "Содержимое заметки в Markdown формате"
                            },
                            "folder": {
                                "type": "string",
                                "description": "Папка для заметки: Ideas, Work, Personal, или Voice Notes",
                                "enum": ["Ideas", "Work", "Personal", "Voice Notes"],
                                "default": "Voice Notes"
                            }
                        },
                        "required": ["title", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_todo_task",
                    "description": "Добавляет новую задачу в файл TODO.md в Obsidian vault. Используй для всего что нужно сделать, купить, не забыть.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "Текст задачи (начинай с глагола)"
                            },
                            "priority": {
                                "type": "string",
                                "description": "Приоритет: high, medium, low",
                                "enum": ["high", "medium", "low"],
                                "default": "medium"
                            },
                            "due_date": {
                                "type": "string",
                                "description": "Дата в формате YYYY-MM-DD или null",
                                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                            }
                        },
                        "required": ["task"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "append_to_note",
                    "description": "Добавляет контент в конец существующей заметки. Используй когда пользователь явно говорит 'добавь к заметке X' или 'дополни'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note_path": {
                                "type": "string",
                                "description": "Путь к заметке относительно vault (например: Work/Project X.md)"
                            },
                            "content": {
                                "type": "string",
                                "description": "Контент для добавления в Markdown"
                            }
                        },
                        "required": ["note_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_notes",
                    "description": "Возвращает список заметок в указанной папке. Используй чтобы найти существующую заметку перед append_to_note или read_note.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "folder": {
                                "type": "string",
                                "description": "Папка для поиска: Ideas, Work, Personal, Voice Notes",
                                "enum": ["Ideas", "Work", "Personal", "Voice Notes"],
                                "default": "Voice Notes"
                            },
                            "search_query": {
                                "type": "string",
                                "description": "Поиск по названию (опционально)"
                            }
                        },
                        "required": ["folder"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_note",
                    "description": "Читает содержимое заметки из vault. Используй когда пользователь ссылается на существующую заметку или хочет узнать её содержимое.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "note_path": {
                                "type": "string",
                                "description": "Полный путь к заметке (папка/файл.md), например: Work/2026-01-20-Project X.md"
                            }
                        },
                        "required": ["note_path"]
                    }
                }
            }
        ]

        # Вызываем OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        # Обрабатываем ответ
        actions = []
        assistant_message = response.choices[0].message

        # Проверяем есть ли tool calls
        if assistant_message.tool_calls:
            # Добавляем ответ ассистента в историю
            messages.append(assistant_message)

            # Выполняем каждый tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Вызываем соответствующую функцию
                if function_name == "create_calendar_event":
                    result = await create_calendar_event(
                        title=function_args["title"],
                        start_date=function_args["start_date"],
                        duration_minutes=function_args.get("duration_minutes", 60),
                        description=function_args.get("description"),
                        location=function_args.get("location"),
                        calendar=self.calendar
                    )
                elif function_name == "list_calendar_events":
                    result = await list_calendar_events(
                        max_results=function_args.get("max_results", 5),
                        calendar=self.calendar
                    )
                elif function_name == "create_note":
                    result = await create_note(
                        title=function_args["title"],
                        content=function_args["content"],
                        folder=function_args.get("folder", "Voice Notes"),
                        vault=self.vault
                    )
                elif function_name == "add_todo_task":
                    result = await add_todo_task(
                        task=function_args["task"],
                        priority=function_args.get("priority", "medium"),
                        due_date=function_args.get("due_date"),
                        vault=self.vault
                    )
                elif function_name == "append_to_note":
                    result = await append_to_note(
                        note_path=function_args["note_path"],
                        content=function_args["content"],
                        vault=self.vault
                    )
                elif function_name == "list_notes":
                    result = await list_notes(
                        folder=function_args["folder"],
                        search_query=function_args.get("search_query"),
                        vault=self.vault
                    )
                elif function_name == "read_note":
                    result = await read_note(
                        note_path=function_args["note_path"],
                        vault=self.vault
                    )
                else:
                    result = f"Неизвестная функция: {function_name}"

                # Сохраняем действие
                actions.append({
                    "function": function_name,
                    "arguments": function_args,
                    "result": result
                })

                # Добавляем результат в историю сообщений
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": result
                })

            # Получаем финальный ответ от модели
            final_response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            summary = final_response.choices[0].message.content
        else:
            # Если tool calls нет, просто берём ответ модели
            summary = assistant_message.content or "Обработка завершена, действий не требуется."

        return {
            "actions": actions,
            "summary": summary
        }
