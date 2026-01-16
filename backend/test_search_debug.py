import asyncio
from app.agents.lightweight_scraper import LightweightScraper
from bs4 import BeautifulSoup
import re

async def test_bing():
    scraper = LightweightScraper()
    html = await scraper.scrape('https://www.bing.com/search?q=python+tutorial&count=5')
    
    # Save HTML to file for inspection
    with open('bing_test.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'\n✓ Saved HTML to bing_test.html ({len(html)} chars)')
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print('\n=== Bing HTML Structure ===')
    print(f'Total links: {len(soup.find_all("a", href=True))}')
    print(f'Cite tags: {len(soup.find_all("cite"))}')
    print(f'H2 tags: {len(soup.find_all("h2"))}')
    print(f'Divs: {len(soup.find_all("div"))}')
    print(f'Scripts: {len(soup.find_all("script"))}')
    
    print('\n=== Checking for JavaScript rendering indicators ===')
    if 'window' in html[:500] or 'var' in html[:500]:
        print('⚠️  Looks like JavaScript-rendered content!')
    
    print('\n=== First 200 chars of HTML ===')
    print(html[:200])

if __name__ == '__main__':
    asyncio.run(test_bing())
