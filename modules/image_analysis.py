# Модуль для анализа изображений

from typing import Any, Dict, Optional

from config import (
    AVAILABLE_IMAGE_ANALYSIS_PROMPTS,
    DEFAULT_GEMINI_MODEL,
    GEMINI_MODELS,
)
from models.analysis import ErrorResponse, ImageAnalysisResponse
from utils.gemini_client import GeminiClient


class ImageAnalysisModule:
    """
    Модуль для анализа изображений с использованием Google Gemini API.
    """

    def __init__(self, model_name: str = DEFAULT_GEMINI_MODEL):
        """
        Инициализация модуля.

        Args:
            model_name: Название модели Gemini для анализа.
        """
        if model_name not in GEMINI_MODELS:
            raise ValueError(
                f"Модель {model_name} не поддерживается. Доступные: {GEMINI_MODELS}"
            )
        self.model_name = model_name
        self.gemini_client = GeminiClient(model_name=model_name)

    def analyze(
        self,
        image_path: str,
        user_prompt: str = "",
        system_instruction_name: Optional[str] = "default",
        system_instruction_override: Optional[str] = None,
        system_instruction_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Анализирует изображение.

        Args:
            image_path: Путь к файлу изображения.
            user_prompt: Пользовательский запрос для анализа.
            system_instruction_name: Имя предустановленной системной инструкции из AVAILABLE_IMAGE_ANALYSIS_PROMPTS.
            system_instruction_override: Строка для переопределения системной инструкции.
            system_instruction_file_path: Путь к файлу с системной инструкцией.

        Returns:
            Словарь с результатом анализа или информацией об ошибке.
        """
        final_system_instruction = None

        # 1. Проверяем, не переопределена ли системная инструкция через файл
        if system_instruction_file_path:
            try:
                with open(system_instruction_file_path, "r", encoding="utf-8") as f:
                    final_system_instruction = f.read()
            except FileNotFoundError:
                return {
                    "error": f"Файл системной инструкции не найден: {system_instruction_file_path}"
                }
            except IOError as e:
                return {"error": f"Ошибка чтения файла системной инструкции: {e}"}
        # 2. Если нет файла, проверяем override
        elif system_instruction_override:
            final_system_instruction = system_instruction_override
        # 3. Если нет override, используем предустановленную по имени
        elif system_instruction_name:
            if system_instruction_name in AVAILABLE_IMAGE_ANALYSIS_PROMPTS:
                final_system_instruction = AVAILABLE_IMAGE_ANALYSIS_PROMPTS[
                    system_instruction_name
                ]
            else:
                return {
                    "error": f"Предустановленный промпт '{system_instruction_name}' не найден. Доступные: {list(AVAILABLE_IMAGE_ANALYSIS_PROMPTS.keys())}"
                }

        # Если ничего не выбрано, используется системная инструкция, встроенная в модель (если есть)
        # или стандартная, которая может быть частью промпта в `contents` в `GeminiClient`

        result = self.gemini_client.analyze_image(
            image_path=image_path,
            user_prompt=user_prompt,
            system_instruction_override=final_system_instruction,  # Передаем сюда собранную инструкцию
        )

        if isinstance(result, ImageAnalysisResponse):
            return result.model_dump()
        if isinstance(result, ErrorResponse):
            return result.model_dump()
        # fallback на случай непредвиденного типа
        return {"error": "Неожиданный формат ответа от Gemini"}


# Пример использования (для тестирования)
if __name__ == "__main__":
    try:
        # Убедись, что GEMINI_API_KEY настроен в .env
        # И что у вас есть файл test_image.jpg в той же директории

        module = ImageAnalysisModule()

        # Пример с предустановленным промптом "default"
        # result = module.analyze(
        #     image_path="test_image.jpg", # Замени на путь к твоему изображению
        #     user_prompt="Опиши, что на этом изображении.",
        #     system_instruction_name="default"
        # )
        # print("Результат анализа (default промпт):")
        # print(result)

        # Пример с техническим промптом
        # result_technical = module.analyze(
        #     image_path="test_image.jpg", # Замени на путь к твоему изображению
        #     user_prompt="Проанализируй дизайн изображения.",
        #     system_instruction_name="technical"
        # )
        # print("\nРезультат анализа (технический промпт):")
        # print(result_technical)

        # Пример с кастомным промптом через override
        # custom_prompt = "Ты — искусствовед. Опиши стиль и художественные особенности этого изображения."
        # result_custom = module.analyze(
        #     image_path="test_image.jpg", # Замени на путь к твоему изображению
        #     user_prompt="Расскажи об этом произведении искусства.",
        #     system_instruction_override=custom_prompt
        # )
        # print("\nРезультат анализа (кастомный промпт):")
        # print(result_custom)

        print("ImageAnalysisModule инициализирован. Примеры закомментированы.")
        print("Чтобы протестировать, раскомментируй и укажи путь к изображению.")

    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
