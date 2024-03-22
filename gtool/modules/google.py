import os
import random
from pathlib import Path
from dotenv import load_dotenv
from lxml import html
from time import sleep
from gtool.settings import GOOGLE_SEARCH, NEWS_CARD_XPATH
from gtool.modules.base import BaseEngine
from gtool.logs import setup_logging


_logger = setup_logging(__name__)

class GoogleEngine(BaseEngine):
    name = "Google"
    help = "Use the Google search engine to scrape news. COOKIE_AEC and COOKIE_SCOS env vars required"

    def __init__(self, sort = False, rotate = False, **kwargs):
        """ * -> force all arguments afterwards are keyword-only
        """
        headers = {
            'authority': 'www.google.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'es-ES,es;q=0.9',
        }
        super().__init__(
            search_url="https://www.google.com/search", 
            headers=headers,
            **kwargs
        )
        self.sort = sort
        self.rotate = rotate

        # Check Google engine required enviroment variables (AOC/SCOS cookies)
        if rotate:
            if not self._rotate_profile():
                return 
        else:    
            load_dotenv() 

        # Check required enviroment variables
        cookies = ['COOKIE_AEC', 'COOKIE_SCOS']
        for cookie in cookies:
            if not os.getenv(cookie):
                _logger.error(f"{cookie} is required.")
                raise Exception(f"{cookie} is required.")


    @classmethod
    def _cli_setup_parser(cls, subparser):
        """
        Arguments
        ----------
        lang: string, optional
            RFC 5646 lang code to force Google to return results only in a specific language 
            Available lang codes = ['af', 'ar', 'hy', 'be', 'bg', 'ca', 'zh-CN', 'zh-TW', 'hr', 
                'cs', 'da', 'nl', 'en', 'eo', 'et', 'tl', 'fi', 'fr', 'de', 'el', 
                'iw', 'hi', 'hu', 'is', 'id', 'it', 'ja', 'ko', 'lv', 'lt', 'no', 
                'fa', 'pl', 'pt', 'ro', 'ru', 'sr', 'sk', 'sl', 'es', 'sw', 'sv', 
                'th', 'tr', 'uk', 'vi'
            ]

        sort: bool, optional
            Flag that indicates whether to sort the search results by date, 
            with the most recent results appearing first. 
            Default is False, meaning results are not sorted by date.

        rotate: bool, optional
            If set, it will choose randomly a .env.N from the ./profiles folder 
            (of the user path). In this folder the user can add multiple .env 
            (AEC/SCOS/PROXY_URL) files with different configurations.
        """
        super()._cli_setup_parser(subparser) # Common parameters between engines like time or range 
        subparser.add_argument(
            '--lang', 
            dest='lang',
            choices=['af', 'ar', 'hy', 'be', 'bg', 'ca', 'zh-CN', 'zh-TW', 'hr', 
                'cs', 'da', 'nl', 'en', 'eo', 'et', 'tl', 'fi', 'fr', 'de', 'el', 
                'iw', 'hi', 'hu', 'is', 'id', 'it', 'ja', 'ko', 'lv', 'lt', 'no', 
                'fa', 'pl', 'pt', 'ro', 'ru', 'sr', 'sk', 'sl', 'es', 'sw', 'sv', 
                'th', 'tr', 'uk', 'vi'
            ],
            help="""Force Google to return results only in a specific language (It only accept some codes from RFC 5646).
            It doesn't work well, the first pages (1-2) always contains sites in the language of your location.
            """
        )
        subparser.add_argument(
            '--sort', 
            dest='sort',
            action='store_true', 
            help="If set, sorts results by date, showing the most recent results first."
        )
        subparser.add_argument(
            '-r','--rotate', 
            dest='rotate',
            action='store_true', 
            help="""
            If set, it will choose randomly a .env.N from the ./profiles folder (of the user path). 
            In this folder the user can add multiple .env (AEC/SCOS/PROXY_URL) files with different configurations.
            """
        )

    @classmethod
    def _cli_from_args(cls, args):
        return cls._cli_filter_args(
            args, 
            lang=args.lang,
            sort=args.sort,
            rotate=args.rotate
        )
    
    def _rotate_profile(self):
        profile_path = Path("./profiles")
        # Check if the profile path exist
        if profile_path.exists() and profile_path.is_dir():
            # Extract all the .env files
            envs = [file.resolve() for file in profile_path.glob(".env*")]
            if not envs:
                _logger.error(" -r/--random argument selected but ./profile don't contains any .env file.")
                return False
            
            env_select = random.choice(envs)
            load_dotenv(env_select)
            _logger.info(f"[Loaded .env: {env_select}]")
            return True

        _logger.error(" -r/--random argument selected but ./profile folder not found.")
        return False

    def _initialize_search(self, session, query):
        """
        Google cookies:
            AEC (Ensure that requests within a browsing session are made by the user, and not by other sites - 6 month)
            SOCS (Is also used to store a user’s state regarding their cookies choices - 13 month)
        """
        
        # Add required cookies
        session.cookies.set("AEC", os.getenv('COOKIE_AEC'), domain=".google.com")
        session.cookies.set("SOCS", os.getenv('COOKIE_SCOS'), domain=".google.com")

        # Conf date filters
        tbs = ''
        if self.time:
            tbs += f'qdr:{self.time}'
        elif self.range:
            start_date = self.range[0].strftime("%-m/%-d/%Y") if self.range[0] else ''
            end_date = self.range[1].strftime("%-m/%-d/%Y") if self.range[1] else ''
            tbs += f'cdr:1,cd_min:{start_date},cd_max:{end_date}'
        if self.sort:
            tbs += ',sbd:1' if tbs else 'sbd:1'  
        if self.lang:
            lr = f'lr:lang_1{self.lang.lower()}'
            tbs += f',{lr}' if tbs else lr   
            self.lang = f'lang_{self.lang.lower()}'   

        return {
            'q': query,
            'tbm': 'nws',
            'biw': 1920, # Screen width
            'bih': 912, # Screen height
            'dpr': 1, # Pixel density
            'tbs': tbs if tbs else None, # Filters (time and sort)
            'lr': self.lang
        }

    def _extract_data(self, response, count, page):
        """ Receive a 200 status_code response from the search engine
        """
        # Parse html content
        tree = html.fromstring(response.content)
        return [
            {
                "url": card_urls[0].get("href").strip().lower(), 
                "position": index+1+count,
                "page": page+1
            }
            for index, card in enumerate(tree.xpath(NEWS_CARD_XPATH))
            if (card_urls := card.xpath(".//a"))
        ]   
