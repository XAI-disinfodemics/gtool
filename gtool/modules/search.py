import random
import requests
from lxml import html
from time import sleep
from gtool.settings import GOOGLE_SEARCH, NEWS_CARD_XPATH
from gtool.logs import setup_logging


_logger = setup_logging(__name__)


def _search(
    session, 
    query, 
    max_pages = 3, 
    tbs = None,
    lang = None,
    bot_sleep_interval = 5.33
):

    results = []
    params = {
        'q': query,
        'tbm': 'nws',
        'biw': 1920, # Screen width
        'bih': 912, # Screen height
        'dpr': 1, # Pixel density
        'tbs': tbs, # Filters (time and sort)
        'lr': lang
    }
    for i in range(0, max_pages):
        
        # Add pagination
        params["start"] = i*10 if i else None

        try:
            response = session.get(GOOGLE_SEARCH, params=params)
            if response.status_code != 200:
                if response.status_code == 429:
                    _logger.error("Captcha block. Try to go to the browser and answer the captcha if it is necessary.")
                else:
                    _logger.error("An error has ocurred during the search. Skipping...")
                return results
        except requests.exceptions.ProxyError as e:
            _logger.error(f"Proxy error {str(e)}")
            return results

        # Parse html content
        tree = html.fromstring(response.content)
        # Extract results
        count = len(results)
        results += [
            {
                "url": card.xpath(".//a")[0].get("href").strip().lower(), 
                "position": index+1+count,
                "page": i+1
            }
            for index, card in enumerate(tree.xpath(NEWS_CARD_XPATH))
        ]    
        if count == len(results):
            _logger.warning("[NO RESULTS FOUND] Skipping...")
            return results

        # Anti-bot detection sleep
        if bot_sleep_interval:
            time = random.uniform(1.5, bot_sleep_interval)
            _logger.info(f"[ANTI-BOT SLEEP]: {time:.3f}")
            sleep(random.uniform(1.5, time))

    return results


def search(
    query, 
    user_agent, 
    cookie_AEC, 
    cookie_SOCS, 
    proxies = None, 
    time = None,
    sort = False,
    lang = None,
    max_pages = 3, 
    bot_sleep_interval = 5.33
):
    """ The main function starts the Google Search to extract news URLs. This 
    function will create the session and prepare any necessary parameters, 
    ultimately returning any URLs found.

    Parameters
    ----------
    query: str
        The search query string that is to be used for the web search.
        
    user_agent: str
        The User-Agent string to use in the HTTP headers when making requests. 
        It helps in defining the browser and the device type that the web crawler is imitating.
        
    cookie_AEC: str
        The value of the AEC cookie. 
        AEC (Ensure that requests within a browsing session are made by the user, and not by other sites - 6 month)
        
    cookie_SOCS: str
        The value of the SOCS cookie. 
        SOCS (Is also used to store a user’s state regarding their cookies choices - 13 month)
        
    proxies: dict, optional
        A dictionary with a proxy information: {"http":"...", "https":"..."}
        Each key-value pair in the dictionary represents the protocol and the address of the proxy.
        Default is None, meaning no proxies are used.
        
    time: str, optional
        Time filter for the search query, Options: 
            - 'h' for last hour.
            - 'd' for last day.
            - 'w' for last week.
            - 'm' for last month. 
            - 'y' for last year.
        Default is None, meaning no time filter is applied.
        
    sort: bool, optional
        Flag that indicates whether to sort the search results by date, 
        with the most recent results appearing first. 
        Default is False, meaning results are not sorted by date.
        
    max_pages: int, optional
        The maximum number of search result pages to crawl. Default is 3.
        
    bot_sleep_interval: float, optional
        The amount of time (in seconds) that the crawler should wait between changing pages, 
        to avoid being blocked by the website due to too many requests. Default is 5.33.

    """
    _logger.info(f"[USER AGENT]: {user_agent}")
    with requests.Session() as s:

        # Add required cookies
        s.cookies.set("AEC", cookie_AEC, domain=".google.com")
        s.cookies.set("SOCS", cookie_SOCS, domain=".google.com")
        
        # Add header
        s.headers.update({
            'authority': 'www.google.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'es-ES,es;q=0.9',
            'user-agent': user_agent
        })

        # Add proxyinfo
        s.proxies = proxies

        # Conf filters (Build the tbs parameter)
        tbs = ''
        if time:
            tbs += f'qdr:{time}'
        if sort:
            tbs += ',sbd:1' if tbs else 'sbd:1'  
        if lang:
            lr = f'lr:lang_1{lang.lower()}'
            tbs += f',{lr}' if tbs else lr   
            lang = f'lang_{lang.lower()}'   

        print(tbs)
        print(lang)  
        
        # Init search
        results = _search(
            session=s,
            query=query,
            max_pages=max_pages,
            tbs=tbs if tbs else None,
            lang=lang,
            bot_sleep_interval=bot_sleep_interval
        )
    return results