import os
import json
import random
import argparse
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from gtool.modules.search import search
from gtool.settings import USER_AGENTS
from gtool.logs import setup_logging, valid_loglevel, configure_logging


_logger = setup_logging(__name__)


def _configure_argparse():
    """Configuration of the parser."""

    parser = argparse.ArgumentParser(
        description='Use the Google search tool.',
    )

    # Global config (proxy, number of threads, f.e)
    group_g = parser.add_argument_group('General optional arguments')
    group_g.add_argument(
        '-L', '--loglevel', 
        dest='loglevel',
        metavar='LEVEL', 
        default='WARNING',
        help=f'log level (default: WARNING). F.e: ["INFO", "DEBUG", "WARNING", "ERROR"]',
        type=valid_loglevel
    )

    group_g.add_argument(
        '-p', '--proxies', 
        dest='proxies', # Name of the variable (args.<name>)
        action = 'store_true', 
        default = False, 
        help = 'Allow proxy. Enviroment variable "PROXY_URL" required.'
    )

    group_g.add_argument(
        '-r','--rotate', 
        dest='rotate',
        action='store_true', 
        help="""
            If set, it will choose randomly a .env.N from the ./profiles folder (of the user path). 
            In this folder the user can add multiple .env (AEC/SCOS/PROXY_URL) files with different configurations.
            """
    )

    group_g.add_argument(
        '-v', '--verbose',
        dest='verbose',
        action='store_true', 
        help='If set, returns a JSON with more information (like the page and position of the URL).',
    )

    # Required arguments
    group_r = parser.add_argument_group('Required arguments')
    group_r.add_argument(
        '-q', '--query',
        dest='query',
        metavar='QUERY',
        type=str, 
        required=True,
        help='Query to search.',
    )

    group_r.add_argument(
        '-f', '--filename',
        dest='filename',
        metavar='FILE', 
        type=str, 
        required=True,
        help='Result filename where all results will be stored (only the name without the extension).',
    )

    # Filter arguments
    group_f = parser.add_argument_group('Filter optional arguments')
    # Define argument for time filter
    time_group = group_f.add_mutually_exclusive_group(required=False)
    time_group.add_argument(
        '--time', 
        dest='time',
        choices=['h', 'd', 'w', 'm', 'y'], 
        help='Specify the time filter. Choices are "h" for last hour, "d" for last day, "w" for last week, "m" for last month, "y" for last year.'
    )
    time_group.add_argument(
        '--range', 
        dest='range',
        type=_valid_range,
        help="""Specify the date range filter in the format 'DD/MM/YYYY - DD/MM/YYYY'. You can leave a the start or the end by using the
        '#' wildcard (For example: '# - DD/MM/YYYY' or 'DD/MM/YYYY - #')
        """
    )
    
    # Define argument for sorting by date
    group_f.add_argument(
        '--sort', 
        dest='sort',
        action='store_true', 
        help="If set, sorts results by date, showing the most recent results first."
    )

    group_f.add_argument(
        '-mp', '--max_pages', 
        dest='pages',
        type=int, 
        default=3, 
        help="The maximum number of search result pages to crawl. Default is 3."
    )

    group_f.add_argument(
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

    # Once parser has been configured, arguments will be parsed
    args = parser.parse_args()
    return args


def _valid_range(date_range_string):
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


def _load_proxy():
    """ In case of arg.proxy = True the proxy url will be read from the enviroment
    variable "PROXY_URL". 

    Returns
    -------
    proxies: dict
        Proxy dict format from requests library ({'http': .... , 'https': ....})
    """
    proxy_url = os.getenv("PROXY_URL")
    if not proxy_url:
        raise ValueError("The environment variable PROXY_URL is not defined.")
    return {
        "http": proxy_url,
        "https": proxy_url
    }


def _rotate_profile():
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


def main():

    # Setup configuration
    args = _configure_argparse()
    configure_logging(args.loglevel)
    proxies = _load_proxy() if args.proxies else {}

    # Check enviroment profile
    if args.rotate:
        if not _rotate_profile():
            return 
    else:    
        load_dotenv() # TODO: if --profile and you have a profile/ folder with a lot of .env.1 it will choose one randomly
    
    # Check required enviroment variables
    cookies = ['COOKIE_AEC', 'COOKIE_SCOS']
    for cookie in cookies:
        if not os.getenv(cookie):
            _logger.error(f"{cookie} is required.")
            return


    ext = '.json' if args.verbose else '.txt'
    with open(args.filename + ext, "w") as file:
        results = search(
            query=args.query,
            user_agent=random.choice(USER_AGENTS),
            proxies=proxies,
            cookie_AEC=os.getenv('COOKIE_AEC'),
            cookie_SOCS=os.getenv('COOKIE_SCOS'),
            time=args.time,
            range=args.range,
            sort=args.sort,
            lang=args.lang,
            max_pages=args.pages
        )

        if args.verbose:
            print(results)
            json.dump(results, file)
        else:
            [file.write(f'{d.get("url", None)}\n') for d in results]

    _logger.info(f"[{len(results)} URLs extracted]")

if __name__ == '__main__':
    main()