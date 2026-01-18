"""
Note Tools for AI Agent

ЗАДАНИЕ 4: Создай function tools для работы с заметками
Инструкции в LEARNING.md
"""

from datetime import datetime
from typing import Annotated
from app.services.github_vault import GitHubVaultService


async def create_note(
    title: Annotated[str, "Заголовок заметки (без расширения .md)"],
    content: Annotated[str, "Содержимое заметки в Markdown формате"],
    folder: Annotated[str, "Папка для заметки: Ideas, Work, Personal, или Voice Notes"] = "Voice Notes",
    vault: GitHubVaultService | None = None
) -> str:
    """
    Создаёт новую заметку в Obsidian vault через GitHub API.
    Используй для сохранения идей, мыслей, рабочих и личных заметок.

    Args:
        title: Заголовок заметки
        content: Содержимое в Markdown
        folder: Папка для размещения (Ideas/Work/Personal/Voice Notes)
        vault: GitHubVaultService instance (будет передан автоматически)

    Returns:
        Сообщение об успешном создании заметки
    """
    if vault is None:
        raise ValueError("GitHubVaultService не передан!")

    # Создаём имя файла с датой
    date = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date}-{title}.md"

    # Создаём путь к файлу
    path = f"{folder}/{filename}"

    # Создаём YAML frontmatter
    frontmatter = f"""---
created: {datetime.now().isoformat()}
source: voice
tags: [voice-note]
---
"""

    # Объединяем всё в полное содержимое
    full_content = frontmatter + "\n\n" + f"# {title}\n\n" + content

    # Создаём файл через GitHub API
    commit_message = f"Add voice note: {title}"
    await vault.create_or_update_file(path, full_content, commit_message)

    return f"Заметка '{title}' создана в {folder}/{filename}"


async def append_to_note(
    note_path: Annotated[str, "Путь к заметке относительно vault (например: Work/Project X.md)"],
    content: Annotated[str, "Контент для добавления в Markdown"],
    vault: GitHubVaultService | None = None
) -> str:
    """
    Добавляет контент в конец существующей заметки.
    Используй когда пользователь явно говорит "добавь к заметке X" или "дополни".
    """
    if vault is None:
        raise ValueError("GitHubVaultService не передан!")

    # Получаем существующий файл
    file_info = await vault.get_file(note_path)

    if file_info is None:
        raise FileNotFoundError(f"Заметка не найдена: {note_path}")

    # Добавляем новый контент в конец
    new_content = file_info.content + "\n\n" + content

    # Обновляем файл
    commit_message = f"Update note: {note_path}"
    await vault.update_file(note_path, new_content, file_info.sha, commit_message)

    return f"Контент добавлен к заметке {note_path}"


async def list_notes(
    folder: Annotated[str, "Папка для поиска: Ideas, Work, Personal, Voice Notes"] = "Voice Notes",
    search_query: Annotated[str | None, "Поиск по названию (опционально)"] = None,
    vault: GitHubVaultService | None = None
) -> str:
    """
    Возвращает список заметок в указанной папке.
    Используй чтобы найти существующую заметку перед append_to_note.
    """
    if vault is None:
        raise ValueError("GitHubVaultService не передан!")

    # Получаем список файлов в папке
    files = await vault.list_folder(folder)

    # Фильтруем только markdown файлы
    notes = [f for f in files if f.endswith('.md')]

    # Если есть поисковый запрос - фильтруем по названию
    if search_query:
        search_lower = search_query.lower()
        notes = [n for n in notes if search_lower in n.lower()]

    # Форматируем результат для AI агента
    if not notes:
        return f"В папке {folder} нет заметок" + (f" по запросу '{search_query}'" if search_query else "")

    notes_list = "\n".join(f"- {note}" for note in notes)
    return f"Заметки в {folder}:\n{notes_list}"
