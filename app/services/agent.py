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

1. ЗАДАЧИ (TODO):
   Триггеры: "нужно", "надо", "не забыть", "купить", "сделать", "позвонить", "отправить", "написать", "проверить", "записаться"
   Действие: add_todo_task()
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

ПРИМЕРЫ:

Пример 1 - Задача:
Вход: "Нужно купить молоко и хлеб завтра утром"
Действие: add_todo_task(task="Купить молоко и хлеб", priority="medium", due_date="2025-01-18")

Пример 2 - Идея:
Вход: "Эээ, знаешь, идея, можно сделать приложение для отслеживания привычек с геймификацией, ну типа как в играх"
Действие: create_note(
    title="Приложение для отслеживания привычек",
    content="## Идея\n\nСоздать приложение для отслеживания привычек с элементами геймификации.\n\n## Детали\n- Игровая механика как в играх\n- Отслеживание прогресса\n- Система наград и достижений",
    folder="Ideas"
)

Пример 3 - Рабочая заметка:
Вход: "Встреча по проекту Альфа. Обсудили новый дизайн. Саша предложил изменить цветовую схему. Нужно показать прототип до пятницы"
Действие: create_note(
    title="Встреча по проекту Альфа",
    content="## Обсуждение\n\n- Новый дизайн проекта\n- Саша предложил изменить цветовую схему\n\n## Action Items\n- [ ] Показать прототип до пятницы",
    folder="Work"
)
+ add_todo_task(task="Показать прототип проекта Альфа", priority="high", due_date="2025-01-24")

Пример 4 - Личная заметка:
Вход: "Сегодня увидел красивый закат. Небо было оранжевое с фиолетовыми облаками. Надо чаще обращать внимание на такие моменты"
Действие: create_note(
    title="Красивый закат",
    content="Сегодня увидел красивый закат. Небо было оранжевое с фиолетовыми облаками.\n\nНадо чаще обращать внимание на такие моменты.",
    folder="Personal"
)

Пример 5 - Смешанный контент:
Вход: "Не забыть позвонить маме в среду. Кстати идея для подарка - можно подарить ей абонемент на йогу"
Действие 1: add_todo_task(task="Позвонить маме", priority="high", due_date="2025-01-22")
Действие 2: create_note(
    title="Идея подарка для мамы",
    content="Абонемент на йогу - мама давно хотела попробовать.",
    folder="Ideas"
)

ПРАВИЛА ОБРАБОТКИ:
- Убирай слова-паразиты: "эээ", "ну", "типа", "вот", "короче", "как бы"
- Убирай повторы и запинки
- Форматируй заметки в Markdown (заголовки, списки, чекбоксы)
- Задачи всегда начинай с глагола в инфинитиве
- Сохраняй важные детали, даты, имена, цифры
- Если непонятно какой тип - создавай заметку в Personal
- Если есть явная задача - всегда добавляй в TODO, даже если есть другой контент
- Всегда отвечай на русском языке
- Будь проактивным: если слышишь срок/дату - добавь due_date
"""


class VoiceNotesAgent:
    """
    AI Agent для обработки голосовых заметок.

    Использует OpenAI API с function calling для выполнения действий.
    """

    def __init__(self, api_key: str, vault_service: GitHubVaultService):
        self.client = AsyncOpenAI(api_key=api_key)
        self.vault = vault_service
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
        from app.tools.note_tools import create_note, append_to_note, list_notes
        from app.tools.todo_tools import add_todo_task
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
                    "description": "Возвращает список заметок в указанной папке. Используй чтобы найти существующую заметку перед append_to_note.",
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
                if function_name == "create_note":
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
