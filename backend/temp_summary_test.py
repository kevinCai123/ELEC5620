import asyncio
from app.services.summary import SummaryService

async def main():
    service = SummaryService()
    summary, fallback, truncated = await service.summarize(url='https://www.sydney.edu.au/units/ELEC5620')
    print('fallback:', fallback, 'truncated:', truncated)
    print(summary.tldr)
    for section in summary.sections:
        print(section.heading, section.bullets)
    for seed in summary.qna_seeds:
        print(seed.q, seed.a_hint)

asyncio.run(main())
