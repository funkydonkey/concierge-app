"""
Whisper Transcriber Service

ЗАДАНИЕ 1: Реализуй транскрипцию аудио через OpenAI Whisper API
Инструкции в LEARNING.md
"""

from openai import AsyncOpenAI


class WhisperTranscriber:
    """Service for audio transcription using OpenAI Whisper."""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def transcribe(self, audio_file_path: str) -> str:
        """
        Транскрибирует аудио файл в текст.

        Args:
            audio_file_path: Путь к аудио файлу

        Returns:
            str: Транскрипция текста

        Raises:
            Exception: Если транскрипция не удалась
        """
        try:
            # Открываем файл в бинарном режиме
            with open(audio_file_path, 'rb') as audio_file:
                # Вызываем Whisper API для транскрипции
                transcription = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"
                )

                return transcription.text

        except FileNotFoundError:
            raise Exception(f"Аудио файл не найден: {audio_file_path}")
        except Exception as e:
            raise Exception(f"Ошибка транскрипции: {str(e)}")
