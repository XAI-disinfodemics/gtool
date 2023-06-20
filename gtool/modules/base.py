import random
import requests
import argparse
import logging
from time import sleep
from datetime import datetime
from abc import ABC, abstractmethod


# Set logger for this file
_logger = logging.getLogger(__name__)

class BaseEngine(ABC):

    def __init__(self, *, 
            search_url,
            headers = {},
            lang = None,
            time = None,
            range = None,
        ):
        self.lang = lang
        self.search_url = search_url
        self.headers = headers
        self.time = time
        self.range = range
        self.PAGE_JUMP = 10 # Number param to jump to the next page


    @classmethod
    def _cli_setup_parser(cls, subparser):
        """
        Arguments
        ----------
        time: str, optional 
            Time filter for the search query, Options: 
                - 'h' for last hour.
                - 'd' for last day.
                - 'w' for last week.
                - 'm' for last month. 
                - 'y' for last year.
            Default is None, meaning no time filter is applied.

        range: tuple, optional
            Specify the date range filter with a tuple of two datetime objects (start_date/None, end_date/None) 
            Default is None, meaning no time filter is applied.
        """
        # Define argument for time filter
        time_group = subparser.add_mutually_exclusive_group(required=False)
        time_group.add_argument(
            '--time', 
            dest='time',
            choices=['h', 'd', 'w', 'm', 'y'], 
            help='Specify the time filter. Choices are "h" for last hour, "d" for last day, "w" for last week, "m" for last month, "y" for last year.'
        )
        time_group.add_argument(
            '--range', 
            dest='range',
            type=cls._valid_range,
            help="""Specify the date range filter in the format 'DD/MM/YYYY - DD/MM/YYYY'. You can ignore the start or the end by using the
            '#' wildcard (For example: '# - DD/MM/YYYY' or 'DD/MM/YYYY - #')
            """
        )

    @classmethod
    def _cli_from_args(cls, args):
        """ Receive a namespace with args from argparse an prepare the instance."""
        return cls._cli_filter_args(args)
    
    @classmethod
    def _cli_filter_args(cls, args, **kwargs):
        """ Filter the args from argparse namespace to choose only those to be
            used.

        Parameters
        ----------
        cls: Class

        args: callable
            Namespace from argparse with all the arguments from the command line

        **kwargs: dict
            Already keyword-only parameters for create the instance.

        Returns
        -------   
        obj: callable
            Instance from cls class
        """
        return cls(
            **kwargs, # Contain args from the child is going to be instanced
            time=args.time, 
            range=args.range
        )
    
    @classmethod
    def _valid_range(cls, date_range_string):
        """Validates the date range entered by the user.

        The function takes a date range in the form:
            - 'DD/MM/YYYY - DD/MM/YYYY'
            - With wildcards as '# - DD/MM/YYYY' or 'DD/MM/YYYY - #'. 
        
        It raises an ArgumentTypeError if the dates are in the wrong order, if a date 
        is greater than today, or if the input cannot be parsed.

        Parameters
        ----------
        date_range_string: str
            The date range to be validated. This should be in the form 'DD/MM/YYYY - DD/MM/YYYY', or with wildcards as 
            '# - DD/MM/YYYY' or 'DD/MM/YYYY - #'. The start date must not be later than the end date.

        Returns
        ----------
        date_range: tuple
            A tuple of two datetime objects (start_date/None, end_date/None) 
        """
        def conver_date(date_string, frm):
            if date_string == "#":
                return None
            else:
                date = datetime.strptime(date_string, frm)
                if date > datetime.now():
                    raise argparse.ArgumentTypeError(f"Not a valid range: {date_string} is grater than today")
                return date

        try:
            frm = "%d/%m/%Y"
            start_date_string, end_date_string = date_range_string.split(' - ')
            start_date = conver_date(start_date_string, frm)
            end_date = conver_date(end_date_string, frm)

            if start_date and end_date and start_date > end_date:
                raise argparse.ArgumentTypeError("Not a valid range: The start date must not be later than the end date.")
        
            return (start_date, end_date)

        except ValueError:
            pass

        msg = "The range contains an invalid date: {0!r}".format(date_range_string)
        raise argparse.ArgumentTypeError(msg)
    
    @abstractmethod
    def _initialize_search(self, session, query, **kwargs):
        """ This method will be created in each Search Engine to initialize any 
        additional information about the session. It will also set up and 
        return its own parameters dictionary.
        """
        pass

    @abstractmethod
    def _extract_data(self, response, count, page):
        pass

    def _search(self, session, params, max_pages, bot_sleep_interval):
        results = []
        for i in range(0, max_pages):
            
            # Add pagination
            params["start"] = i*self.PAGE_JUMP if i else None

            try:
                response = session.get(self.search_url, params=params)
                if response.status_code != 200:
                    if response.status_code == 429:
                        _logger.error("Captcha block. Try to go to the browser and answer the captcha if it is necessary.")
                    else:
                        print(params)
                        _logger.error(f"An error has ocurred during the search [{response.status_code}].  Skipping...")
                    break
            except requests.exceptions.ProxyError as e:
                _logger.error(f"Proxy error {str(e)}")
                break

            # Extract results
            count = len(results)
            results += self._extract_data(response, count, i)
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
        self,
        query, 
        max_pages = 3, 
        user_agent = None,
        proxies = None,
        bot_sleep_interval = 5.33,
        **kwargs
    ):
        """ The main function starts the search engine to extract news URLs. This 
        function will create the session and prepare any necessary parameters, 
        ultimately returning any URLs found.

        Parameters
        ----------
        query: str
            The search query string that is to be used for the web search.

        max_pages: int, optional
            The maximum number of search result pages to crawl. Default is 3.

        proxies: dict, optional
            A dictionary with a proxy information: {"http":"...", "https":"..."}
            Each key-value pair in the dictionary represents the protocol and the address of the proxy.
            Default is None, meaning no proxies are used.

        user_agent: str
            The User-Agent string to use in the HTTP headers when making requests. 
            It helps in defining the browser and the device type that the web crawler is imitating.
            
        bot_sleep_interval: float, optional
            The amount of time (in seconds) that the crawler should wait between changing pages, 
            to avoid being blocked by the website due to too many requests. Default is 5.33.

        kwargs: dict, optional
            Extra keywords arguments to use in the _initialize_search method
            to allow different engines to use extra data without repeating code.
        """
        _logger.info(f"[USER AGENT]: {user_agent}")
        with requests.Session() as s:

            # Add proxyinfo
            s.proxies = proxies

            # Add headers
            s.headers.update(dict(self.headers, **{'user-agent': user_agent}))

            # Initialize search (params, headers, etc..)
            params = self._initialize_search(s, query, **kwargs)

            # Init search
            results = self._search(s, params, max_pages, bot_sleep_interval)

        return results