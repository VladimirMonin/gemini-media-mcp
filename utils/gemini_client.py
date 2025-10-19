# Клиент для взаимодействия с Google Gemini API

import json
from typing import Optional, Union
from PIL import Image
from google.genai import types, Client

from config import GEMINI_API_KEY, DEFAULT_GEMINI_MODEL
from models.analysis import ImageAnalysisResponse, ErrorResponse


class GeminiClient:
    """
    Обертка для клиента Google Gemini API.
    """

    def __init__(self, model_name: str = DEFAULT_GEMINI_MODEL):
        self.model_name = model_name
        self.client = Client(api_key=GEMINI_API_KEY)

    def analyze_image(
        self,
        image_path: str,
        user_prompt: str,
        system_instruction_override: Optional[str] = None,
        system_instruction_file_path: Optional[str] = None,
    ) -> Union[ImageAnalysisResponse, ErrorResponse]:
        """
        Анализирует изображение с помощью Gemini API.

        Args:
            image_path: Путь к файлу изображения.
            user_prompt: Пользовательский запрос для анализа.
            system_instruction_override: Переопределение системной инструкции.
            system_instruction_file_path: Путь к файлу с системной инструкцией.

        Returns:
            Словарь с результатом анализа или информацией об ошибке.
        """
        try:
            # Определение финальной системной инструкции
            final_system_instruction = None
            if system_instruction_file_path:
                try:
                    with open(system_instruction_file_path, "r", encoding="utf-8") as f:
                        final_system_instruction = f.read()
                except FileNotFoundError:
                    return ErrorResponse(
                        error="Файл системной инструкции не найден",
                        details=system_instruction_file_path,
                    )
                except IOError as e:
                    return ErrorResponse(
                        error="Ошибка чтения файла системной инструкции",
                        details=str(e),
                    )
            elif system_instruction_override:
                final_system_instruction = system_instruction_override

            # Загрузка изображения через PIL
            try:
                image = Image.open(image_path)
            except FileNotFoundError:
                return ErrorResponse(
                    error="Файл изображения не найден",
                    details=image_path,
                )
            except IOError as e:
                return ErrorResponse(
                    error="Ошибка чтения файла изображения",
                    details=str(e),
                )

            # Формирование запроса
            prompt_content = (
                user_prompt if user_prompt else "Проанализируй изображение."
            )

            # Формируем contents с текстом и изображением
            contents = [prompt_content, image]

            # Создаём конфигурацию
            config_params = {
                "temperature": 0.7,
                "max_output_tokens": 2048,
                "safety_settings": [
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    ),
                ],
                "response_mime_type": "application/json",
                "response_schema": ImageAnalysisResponse,
            }

            # Добавляем системную инструкцию если есть
            if final_system_instruction:
                config_params["system_instruction"] = final_system_instruction

            config = types.GenerateContentConfig(**config_params)

            # Отправка запроса с использованием нового API
            response = self.client.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )

            # Проверка на наличие ошибок в ответе
            if hasattr(response, "candidates") and response.candidates:
                # Получаем текст ответа
                response_text = (response.text or "").strip()

                # Пытаемся распарсить JSON
                try:
                    # Убираем markdown-обертку ```json ... ``` если есть
                    if response_text.startswith("```json"):
                        response_text = response_text[len("```json") :].strip()
                    if response_text.endswith("```"):
                        response_text = response_text[: -len("```")].strip()

                    result_dict = json.loads(response_text)
                    return ImageAnalysisResponse(**result_dict)
                except json.JSONDecodeError:
                    # Если ответ не в JSON, возвращаем как есть, но с пометкой
                    return ErrorResponse(
                        error="Ответ не в формате JSON",
                        raw_response=response_text,
                    )
            else:
                # Обработка случаев, когда candidates не возвращены
                if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                    feedback = response.prompt_feedback
                    if hasattr(feedback, "block_reason") and feedback.block_reason:
                        return ErrorResponse(
                            error="Запрос заблокирован",
                            details=str(feedback.block_reason),
                        )
                return ErrorResponse(error="Не удалось получить ответ от модели Gemini")

        except Exception as e:
            # Общая обработка ошибок
            return ErrorResponse(
                error="Произошла непредвиденная ошибка при анализе изображения",
                details=str(e),
            )

    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Генерирует текст на основе промпта.
        """
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt, **kwargs
        )
        return response.text or ""


# Пример использования (для тестирования)
if __name__ == "__main__":
    # Убедись, что GEMINI_API_KEY настроен в .env
    # И что у вас есть файл test_image.jpg в той же директории
    try:
        client = GeminiClient()

        # Создать тестовый файл изображения для примера (просто черный прямоугольник)
        # В реальном использовании пользователь предоставит свой путь
        test_image_path = "test_image.jpg"
        # with open(test_image_path, "wb") as f:
        #     f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.'', #(",(7),01444'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x01\x01\x00\x02\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9') # Это пример JPEG заголовка, не полноценное изображение

        # Для настоящего теста нужно иметь реальное изображение
        # if os.path.exists(test_image_path):
        #     result = client.analyze_image(
        #         image_path=test_image_path,
        #         user_prompt="Опиши, что на этом изображении.",
        #         system_instruction_override="Ты — дружелюбный помощник."
        #     )
        #     print("Результат анализа:")
        #     print(json.dumps(result, indent=2, ensure_ascii=False))
        # else:
        #     print(f"Тестовое изображение {test_image_path} не найдено. Пропуск теста.")
        print(
            "GeminiClient инициализирован. Тест анализа изображения требует реального файла."
        )

    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
