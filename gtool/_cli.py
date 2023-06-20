import os
import json
import random
import argparse
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from gtool.modules.base import BaseEngine
from gtool.settings import USER_AGENTS
from gtool.logs import setup_logging, valid_loglevel, configure_logging


_logger = setup_logging(__name__)


def _configure_argparse():
    """Configuration of the parser."""

    parser = argparse.ArgumentParser(
        description='Use the Google search tool.',
    )

    # Global config (proxy, number of pages, f.e)
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
        '-mp', '--max_pages', 
        dest='pages',
        type=int, 
        default=3, 
        help="The maximum number of search result pages to crawl. Default is 3."
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

    # Choose main engine
    subparsers = parser.add_subparsers(
        dest = 'engine', 
        title = 'Ntool actions (required)', 
        required = True
    )
    for cls in BaseEngine.__subclasses__():
        subparser = subparsers.add_parser(cls.name, help=cls.help, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cls._cli_setup_parser(subparser)
        # When action TweetSearch is choosen, the following line add to the args list
        # the args.cls with the value of the class related to that class
        subparser.set_defaults(cls=cls) 

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


def main():

    # Setup configuration
    args = _configure_argparse()
    configure_logging(args.loglevel)
    proxies = _load_proxy() if args.proxies else {}
   
    # Initialize class from choosen egine
    engine_obj = args.cls._cli_from_args(args)

    ext = '.json' if args.verbose else '.txt'
    with open(args.filename + ext, "w") as file:

        try:
            results = engine_obj.search(
                query=args.query,
                max_pages=args.pages,
                user_agent=random.choice(USER_AGENTS),
                proxies=proxies,
            )
        except Exception as e:
            _logger.error(e)
            return 

        if args.verbose:
            json.dump(results, file)
        else:
            [file.write(f'{d.get("url", None)}\n') for d in results]

    _logger.info(f"[{len(results)} URLs extracted]")

if __name__ == '__main__':
    main()