# Асинхронность и конкурентность в MCP серверах и Gemini API

## Обзор исследования

Этот документ содержит результаты исследования асинхронных возможностей Google GenAI Python SDK и MCP Python SDK для создания высокопроизводительных локальных MCP серверов с поддержкой конкурентных запросов от разных агентов.

## 🔧 Технические возможности

### 1. Google GenAI Python SDK - Асинхронность

#### Асинхронный клиент с конкурентными запросами
```python
from google import genai
import asyncio

async def main():
    # Создание асинхронного клиента
    async with genai.Client(api_key='your-api-key').aio as aclient:
        # Конкурентные запросы к Gemini API
        tasks = [
            aclient.models.generate_content(
                model='gemini-2.5-flash',
                contents='What is AI?'
            ),
            aclient.models.generate_content(
                model='gemini-2.5-flash',
                contents='What is ML?'
            ),
            aclient.models.generate_content(
                model='gemini-2.5-flash',
                contents='What is DL?'
            )
        ]

        # Параллельное выполнение всех запросов
        results = await asyncio.gather(*tasks)
        for i, result in enumerate(results):
            print(f"Response {i+1}: {result.text[:100]}...")

asyncio.run(main())
```

#### Асинхронное потоковое содержимое
```python
async for chunk in await client.aio.models.generate_content_stream(
    model='gemini-2.5-flash', 
    contents='Tell me a story in 300 words.'
):
    print(chunk.text, end='')
```

#### Оптимизация производительности с aiohttp
```python
# Установка: pip install google-genai[aiohttp]
http_options = types.HttpOptions(
    async_client_args={'cookies': ..., 'ssl': ...},
)

client = Client(..., http_options=http_options)
```

### 2. MCP Python SDK - Асинхронные инструменты

#### Асинхронные инструменты с прогресс-репортами
```python
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
import asyncio

mcp = FastMCP(name="Video Analyzer")

@mcp.tool()
async def analyze_video(
    video_path: str,
    ctx: Context[ServerSession, None],
    frame_count: int = 10,
    audio_bitrate: int = 32
) -> str:
    """Асинхронный анализ видео с прогрессом."""
    
    await ctx.info(f"Начинаю анализ: {video_path}")
    
    # Асинхронное извлечение кадров
    await ctx.report_progress(progress=0.2, message="Извлечение кадров...")
    frames = await extract_frames_async(video_path, frame_count)
    
    # Асинхронное извлечение аудио
    await ctx.report_progress(progress=0.5, message="Извлечение аудио...")
    audio = await extract_audio_async(video_path, audio_bitrate)
    
    # Асинхронный запрос к Gemini
    await ctx.report_progress(progress=0.8, message="Анализ в Gemini...")
    result = await analyze_with_gemini_async(frames, audio)
    
    await ctx.report_progress(progress=1.0, message="Анализ завершен")
    return result
```

#### Управление множественными сессиями
```python
from mcp import ClientSessionGroup, StdioServerParameters

async def manage_multiple_agents():
    """Управление конкурентными запросами от разных агентов."""
    
    async with ClientSessionGroup() as group:
        # Подключение к серверам
        await group.connect_to_server(weather_server)
        await group.connect_to_server(database_server)
        
        # Конкурентные вызовы инструментов
        tasks = [
            group.call_tool("weather_server_get_weather", {"city": "London"}),
            group.call_tool("database_server_query_users", {"limit": 10}),
            group.call_tool("video_analyzer_analyze_video", {"video_path": "test.mp4"})
        ]
        
        results = await asyncio.gather(*tasks)
        return results
```

## 🚀 Архитектура для конкурентных запросов

### 1. Множественные MCP серверы в одном приложении
```python
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

# Создание нескольких MCP серверов
video_mcp = FastMCP(name="VideoAnalyzer")
audio_mcp = FastMCP(name="AudioAnalyzer")

@video_mcp.tool()
async def analyze_video(video_path: str, ctx: Context) -> str:
    """Анализ видео."""
    return await process_video_async(video_path)

@audio_mcp.tool()
async def analyze_audio(audio_path: str, ctx: Context) -> str:
    """Анализ аудио."""
    return await process_audio_async(audio_path)

# Монтирование серверов
app = Starlette(
    routes=[
        Mount("/video", app=video_mcp.streamable_http_app()),
        Mount("/audio", app=audio_mcp.streamable_http_app()),
    ]
)
```

### 2. Асинхронная обработка видео с прогрессом
```python
@mcp.tool()
async def batch_analyze_videos(
    video_paths: list[str],
    ctx: Context[ServerSession, None],
    frame_count: int = 10
) -> list[str]:
    """Пакетный анализ видео с конкурентной обработкой."""
    
    total_videos = len(video_paths)
    results = []
    
    for i, video_path in enumerate(video_paths):
        progress = (i + 1) / total_videos
        
        await ctx.report_progress(
            progress=progress,
            message=f"Обработка видео {i+1}/{total_videos}: {video_path}"
        )
        
        # Асинхронная обработка каждого видео
        result = await analyze_single_video_async(video_path, frame_count)
        results.append(result)
    
    return results

async def analyze_single_video_async(video_path: str, frame_count: int) -> str:
    """Асинхронный анализ одного видео."""
    # Асинхронное извлечение кадров
    frames_task = asyncio.create_task(extract_frames_async(video_path, frame_count))
    
    # Асинхронное извлечение аудио
    audio_task = asyncio.create_task(extract_audio_async(video_path))
    
    # Ожидание завершения обеих задач
    frames, audio = await asyncio.gather(frames_task, audio_task)
    
    # Асинхронный запрос к Gemini
    return await analyze_with_gemini_async(frames, audio)
```

## 📊 Производительность и оптимизация

### 1. Конкурентные запросы к Gemini API
```python
async def concurrent_gemini_requests(prompts: list[str]) -> list[str]:
    """Конкурентные запросы к Gemini API."""
    async with genai.Client().aio as aclient:
        tasks = [
            aclient.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            for prompt in prompts
        ]
        
        results = await asyncio.gather(*tasks)
        return [result.text for result in results]
```

### 2. Ограничения и рекомендации

#### Rate Limits Gemini API:
- **Запросы в секунду:** Зависит от модели и аккаунта
- **Токены в минуту:** Ограничения по токенам
- **Параллельные запросы:** Рекомендуется использовать пулы соединений

#### Оптимизация MCP сервера:
```python
# Настройка для высокой нагрузки
mcp = FastMCP(
    name="HighLoadServer",
    settings=FastMCPSettings(
        max_concurrent_requests=50,  # Максимум конкурентных запросов
        request_timeout=300,         # Таймаут 5 минут
    )
)
```

## 🎯 Практические примеры

### 1. Асинхронный видео-анализатор для MCP
```python
@mcp.tool()
async def analyze_video_async(
    video_path: str,
    ctx: Context[ServerSession, None],
    frame_mode: str = "total",
    frame_count: int = 10,
    audio_bitrate: int = 32
) -> str:
    """Полностью асинхронный анализ видео."""
    
    await ctx.info(f"Начинаю асинхронный анализ: {video_path}")
    
    # Создание конкурентных задач
    frames_task = asyncio.create_task(
        extract_frames_async(video_path, frame_mode, frame_count)
    )
    audio_task = asyncio.create_task(
        extract_audio_async(video_path, audio_bitrate)
    )
    
    # Ожидание завершения обеих задач
    frames, audio = await asyncio.gather(frames_task, audio_task)
    
    await ctx.report_progress(progress=0.7, message="Данные подготовлены")
    
    # Асинхронный запрос к Gemini
    result = await send_to_gemini_async(frames, audio, ctx)
    
    await ctx.report_progress(progress=1.0, message="Анализ завершен")
    return result

async def send_to_gemini_async(frames: list, audio: dict, ctx: Context) -> str:
    """Асинхронная отправка данных в Gemini."""
    async with genai.Client().aio as aclient:
        contents = [
            "Проанализируй видео по кадрам и аудио:",
            *[types.Part.from_bytes(frame, 'image/webp') for frame in frames],
            types.Part.from_bytes(audio['base64'], 'audio/ogg')
        ]
        
        response = await aclient.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        
        return response.text
```

### 2. Множественные агенты с изолированными сессиями
```python
async def handle_multiple_agents():
    """Обработка запросов от разных агентов."""
    async with ClientSessionGroup() as group:
        # Каждый агент получает свою сессию
        agent_sessions = {}
        
        for agent_id in agent_ids:
            session = await group.create_session()
            agent_sessions[agent_id] = session
        
        # Конкурентная обработка запросов агентов
        agent_tasks = []
        for agent_id, session in agent_sessions.items():
            task = process_agent_request(session, agent_requests[agent_id])
            agent_tasks.append(task)
        
        results = await asyncio.gather(*agent_tasks)
        return dict(zip(agent_sessions.keys(), results))
```

## ✅ Выводы и рекомендации

### Подтвержденные возможности:

1. **✅ Google GenAI SDK полностью асинхронный**
   - Поддерживает `async/await` паттерны
   - Конкурентные запросы через `asyncio.gather()`
   - Потоковая обработка через `async for`
   - Оптимизация с `aiohttp`

2. **✅ MCP Python SDK поддерживает асинхронность**
   - Асинхронные инструменты с `@mcp.tool()`
   - Прогресс-репорты и логирование
   - Управление множественными сессиями
   - Конкурентные запросы от разных агентов

3. **✅ Производительность для реальных кейсов**
   - Обработка видео без блокировки
   - Множественные агенты работают параллельно
   - Эффективное использование ресурсов

### Рекомендации для реализации:

1. **Используйте асинхронные инструменты** для длительных операций
2. **Применяйте ClientSessionGroup** для управления множественными агентами
3. **Оптимизируйте с aiohttp** для лучшей производительности
4. **Используйте прогресс-репорты** для пользовательского опыта
5. **Учитывайте rate limits** Gemini API при конкурентных запросах

**Итог:** Технически возможно создавать высокопроизводительные локальные MCP серверы с полной поддержкой асинхронности и конкурентных запросов от разных агентов без блокировки операций.
