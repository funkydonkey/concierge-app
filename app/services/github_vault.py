"""
GitHub Vault Service

ЗАДАНИЕ 2: Реализуй работу с GitHub API для управления файлами в Obsidian vault
Инструкции в LEARNING.md
"""

import httpx
import base64
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Информация о файле в репозитории."""
    path: str
    sha: str
    content: str | None = None


class GitHubVaultService:
    """
    Сервис для работы с Obsidian vault через GitHub API.

    Использует GitHub Contents API для создания/обновления файлов.
    """

    def __init__(
        self,
        token: str,
        repo_owner: str,
        repo_name: str,
        branch: str = "main"
    ):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def get_file(self, path: str) -> FileInfo | None:
        """
        Получает содержимое файла из репозитория.

        Args:
            path: Путь к файлу относительно корня vault

        Returns:
            FileInfo с содержимым и SHA, или None если файл не найден
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/contents/{path}?ref={self.branch}"
            response = await client.get(url, headers=self.headers)

            # Если файл не найден - возвращаем None
            if response.status_code == 404:
                return None

            # Проверяем успешность запроса
            response.raise_for_status()

            data = response.json()
            sha = data["sha"]
            content_base64 = data["content"]

            # Декодируем содержимое из base64
            decoded_content = base64.b64decode(content_base64).decode('utf-8')

            return FileInfo(path=path, sha=sha, content=decoded_content)

    async def create_file(
        self,
        path: str,
        content: str,
        commit_message: str
    ) -> FileInfo:
        """
        Создаёт новый файл в репозитории.

        Args:
            path: Путь для нового файла
            content: Содержимое файла (текст)
            commit_message: Сообщение коммита

        Returns:
            FileInfo созданного файла

        Raises:
            Exception: Если файл уже существует (409)
        """
        # Кодируем содержимое в base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        body = {
            "message": commit_message,
            "content": encoded_content,
            "branch": self.branch
        }

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/contents/{path}"
            response = await client.put(url, headers=self.headers, json=body)

            # Проверяем успешность запроса (409 если файл существует)
            response.raise_for_status()

            data = response.json()
            sha = data["content"]["sha"]

            return FileInfo(path=path, sha=sha, content=content)

    async def update_file(
        self,
        path: str,
        content: str,
        sha: str,
        commit_message: str
    ) -> FileInfo:
        """
        Обновляет существующий файл.

        Args:
            path: Путь к файлу
            content: Новое содержимое
            sha: SHA текущей версии (для оптимистичной блокировки)
            commit_message: Сообщение коммита

        Returns:
            FileInfo обновлённого файла

        Raises:
            Exception: Если SHA не совпадает (409 конфликт)
        """
        # Кодируем содержимое в base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        body = {
            "message": commit_message,
            "content": encoded_content,
            "sha": sha,  # SHA для оптимистичной блокировки
            "branch": self.branch
        }

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/contents/{path}"
            response = await client.put(url, headers=self.headers, json=body)

            # Проверяем успешность (409 если SHA не совпадает)
            response.raise_for_status()

            data = response.json()
            new_sha = data["content"]["sha"]

            return FileInfo(path=path, sha=new_sha, content=content)

    async def list_folder(self, folder_path: str) -> list[str]:
        """
        Получает список файлов в папке.

        Args:
            folder_path: Путь к папке

        Returns:
            Список ИМЁН файлов (без пути к папке)
        """
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/contents/{folder_path}?ref={self.branch}"
            response = await client.get(url, headers=self.headers)

            # Проверяем успешность запроса
            response.raise_for_status()

            data = response.json()

            # Фильтруем только файлы (не директории) и возвращаем только имена
            files = [item["name"] for item in data if item["type"] == "file"]

            return files

    async def create_or_update_file(
        self,
        path: str,
        content: str,
        commit_message: str
    ) -> FileInfo:
        """
        Создаёт файл или обновляет если существует.

        Удобный метод который сам определяет create или update.
        """
        existing = await self.get_file(path)
        if existing:
            return await self.update_file(path, content, existing.sha, commit_message)
        else:
            return await self.create_file(path, content, commit_message)
