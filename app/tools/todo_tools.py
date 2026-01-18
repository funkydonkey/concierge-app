"""
TODO Tools for AI Agent

ЗАДАНИЕ 4: Создай function tool для работы с TODO-листом
Инструкции в LEARNING.md
"""

from typing import Annotated
from app.services.github_vault import GitHubVaultService


async def add_todo_task(
    task: Annotated[str, "Текст задачи (начинай с глагола)"],
    priority: Annotated[str, "Приоритет: high, medium, low"] = "medium",
    due_date: Annotated[str | None, "Дата в формате YYYY-MM-DD или None"] = None,
    vault: GitHubVaultService | None = None
) -> str:
    """
    Добавляет новую задачу в файл TODO.md в Obsidian vault.
    Используй для всего что нужно сделать, купить, не забыть.

    Задача добавляется в соответствующую секцию по приоритету.

    Args:
        task: Текст задачи (начинать с глагола)
        priority: high, medium, или low
        due_date: Опциональная дата в формате YYYY-MM-DD
        vault: GitHubVaultService instance

    Returns:
        Сообщение об успешном добавлении задачи
    """
    if vault is None:
        raise ValueError("GitHubVaultService не передан!")

    # Получаем текущий TODO.md или создаём новый
    todo_file = await vault.get_file("TODO.md")

    if todo_file is None:
        # Создаём новый TODO.md с базовой структурой
        content = INITIAL_TODO_TEMPLATE
        commit_message = "Create TODO.md"
        await vault.create_file("TODO.md", content, commit_message)
        todo_file = await vault.get_file("TODO.md")

    # Создаём строку задачи
    task_line = f"- [ ] {task}"
    if due_date:
        task_line += f" (due: {due_date})"

    # Определяем заголовок секции по приоритету
    priority_headers = {
        "high": "## 🔴 High Priority",
        "medium": "## 🟡 Medium Priority",
        "low": "## 🟢 Low Priority"
    }

    header = priority_headers.get(priority.lower(), "## 🟡 Medium Priority")

    # Разбиваем содержимое по строкам
    lines = todo_file.content.split('\n')

    # Находим индекс нужной секции
    section_index = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            section_index = i
            break

    if section_index is None:
        raise ValueError(f"Секция {header} не найдена в TODO.md")

    # Вставляем задачу после заголовка секции
    # Пропускаем пустую строку после заголовка если она есть
    insert_index = section_index + 1
    if insert_index < len(lines) and lines[insert_index].strip() == "":
        insert_index += 1

    # Вставляем задачу
    lines.insert(insert_index, task_line)

    # Собираем обратно в строку
    new_content = '\n'.join(lines)

    # Обновляем файл
    commit_message = f"Add TODO: {task}"
    await vault.update_file("TODO.md", new_content, todo_file.sha, commit_message)

    return f"Задача '{task}' добавлена в TODO (приоритет: {priority})"


# Пример начальной структуры TODO.md для создания нового файла
INITIAL_TODO_TEMPLATE = """# 📋 TODO

## 🔴 High Priority

## 🟡 Medium Priority

## 🟢 Low Priority

## ✅ Completed
"""
