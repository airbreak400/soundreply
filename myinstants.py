import aiohttp
import parsel
from user_agent import generate_user_agent

SEARCH_URL = "https://www.myinstants.com/en/search/?name={}"
TOP_US_URL = "https://www.myinstants.com/en/index/us/"
MEDIA_URL = "https://www.myinstants.com{}"


class MyInstantsApiException(Exception):
    """General exception for myinstants api"""
    pass


async def get_top_us_sounds():
    """AQSHdagi TOP tovushlarni olish
    
    Returns:
        List of dicts: [{'text': 'Tovush nomi', 'url': 'URL'}]
    """
    headers = {
        "User-Agent": generate_user_agent()
    }
    
    data = None
    async with aiohttp.ClientSession() as session:
        async with session.get(TOP_US_URL, headers=headers, timeout=15) as response:
            if response.status == 200:
                data = await response.text()
            else:
                return []

    sel = parsel.Selector(data)
    names = sel.css(".instant .instant-link::text").getall()
    links = sel.css(
        ".instant .small-button::attr(onclick),.instant .small-button::attr(onmousedown)"
    ).re(r"play\('(.*?)',")

    return [
        {
            "text": text.strip(),
            "url": MEDIA_URL.format(url),
        }
        for text, url in zip(names, links)
    ]


async def search_instants(query):
    """MyInstants.com dan tovush qidirish
    
    Args:
        query: Qidiruv so'zi
        
    Returns:
        List of dicts: [{'text': 'Tovush nomi', 'url': 'URL'}]
    """
    query_string = (
        "+".join(query) if isinstance(query, list) else query.replace(" ", "+")
    )

    url = SEARCH_URL.format(query_string)
    headers = {
        "User-Agent": generate_user_agent()
    }
    
    data = None
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                data = await response.text()
            else:
                return []

    sel = parsel.Selector(data)
    names = sel.css(".instant .instant-link::text").getall()
    links = sel.css(
        ".instant .small-button::attr(onclick),.instant .small-button::attr(onmousedown)"
    ).re(r"play\('(.*?)',")

    return [
        {
            "text": text.strip(),
            "url": MEDIA_URL.format(url),
        }
        for text, url in zip(names, links)
    ]