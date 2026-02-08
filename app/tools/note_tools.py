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
    folder: Annotated[str | None, "Папка для поиска: Ideas, Work, Personal, Voice Notes. Если None - поиск во всех папках"] = None,
    search_query: Annotated[str | None, "Поиск по названию (опционально)"] = None,
    vault: GitHubVaultService | None = None
) -> str:
    """
    Возвращает список заметок в указанной папке или во всех папках (если folder=None).
    Используй чтобы найти существующую заметку перед append_to_note или read_note.
    """
    if vault is None:
        raise ValueError("GitHubVaultService не передан!")

    all_notes = []

    # Если папка не указана - ищем во всех папках
    if folder is None:
        folders = ["Ideas", "Work", "Personal", "Voice Notes"]
        for f in folders:
            try:
                files = await vault.list_folder(f)
                # Добавляем путь с папкой к каждой заметке
                notes_with_path = [f"{f}/{file}" for file in files if file.endswith('.md')]
                all_notes.extend(notes_with_path)
            except Exception:
                # Игнорируем ошибки (папка может не существовать)
                continue
    else:
        # Ищем в конкретной папке
        files = await vault.list_folder(folder)
        all_notes = [f"{folder}/{file}" for file in files if file.endswith('.md')]

    # Если есть поисковый запрос - фильтруем по названию
    if search_query:
        search_lower = search_query.lower()
        all_notes = [n for n in all_notes if search_lower in n.lower()]

    # Форматируем результат для AI агента
    if not all_notes:
        location = f"папке {folder}" if folder else "vault"
        return f"В {location} нет заметок" + (f" по запросу '{search_query}'" if search_query else "")

    notes_list = "\n".join(f"- {note}" for note in all_notes)
    location = folder if folder else "всех папках"
    return f"Заметки в {location}:\n{notes_list}"


async def read_note(
    note_path: Annotated[str, "Путь к заметке относительно vault (например: Work/2026-01-20-Project X.md)"],
    vault: GitHubVaultService | None = None
) -> str:
    """
    Читает содержимое заметки из Obsidian vault.
    Используй когда пользователь ссылается на существующую заметку или хочет узнать её содержимое.

    Args:
        note_path: Полный путь к заметке (папка/файл.md)
        vault: GitHubVaultService instance (будет передан автоматически)

    Returns:
        Содержимое заметки в Markdown формате

    Примеры использования:
    - "Что в заметке про проект X?"
    - "Прочитай мою заметку про встречу"
    - "Какие идеи у меня были про приложение?" (сначала list_notes, потом read_note)
    """
    if vault is None:
        raise ValueError("GitHubVaultService не передан!")

    # Получаем файл
    file_info = await vault.get_file(note_path)

    if file_info is None:
        return f"❌ Заметка не найдена: {note_path}\n\nИспользуй list_notes() чтобы найти доступные заметки."

    # Возвращаем содержимое
    return f"📄 Заметка: {note_path}\n\n{file_info.content}"
