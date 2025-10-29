import asyncio
from app.services.llm import LLMService

async def main():
    svc = LLMService()
    result = await svc.summarize('Machine learning enables computers to learn from data. It improves predictions over time by learning from labeled examples.')
    print(result)

asyncio.run(main())
