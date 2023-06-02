import os
import json
import random
import argparse
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
        help='Result filename where all results will be stored.',
    )

    # Filter arguments
    group_f = parser.add_argument_group('Filter optional arguments')
    # Define argument for time filter
    group_f.add_argument(
        '--time', 
        dest='time',
        choices=['h', 'd', 'w', 'm', 'y'], 
        help='Specify the time filter. Choices are "h" for last hour, "d" for last day, "w" for last week, "m" for last month, "y" for last year.'
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

    # Once parser has been configured, arguments will be parsed
    args = parser.parse_args()
    return args


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

    with open(args.filename, "w") as file:
        results = search(
            query=args.query,
            user_agent=random.choice(USER_AGENTS),
            proxies=proxies,
            cookie_AEC=os.getenv('COOKIE_AEC'),
            cookie_SOCS=os.getenv('COOKIE_SCOS'),
            time=args.time,
            sort=args.sort,
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