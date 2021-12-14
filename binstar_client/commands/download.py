"""
Usage:
    anaconda download notebook
    anaconda download user/notebook
"""

from __future__ import unicode_literals

import argparse
import logging

from binstar_client import errors
from binstar_client.utils import get_server_api
from binstar_client.utils.config import PackageType
from binstar_client.utils.notebook import Downloader, parse, has_environment

logger = logging.getLogger("binstar.download")


def add_parser(subparsers):
    description = 'Download notebooks from your Anaconda repository'
    parser = subparsers.add_parser(
        'download',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=description,
        description=description,
        epilog=__doc__
    )

    parser.add_argument(
        'handle',
        help="user/notebook",
        action='store'
    )

    parser.add_argument(
        '-f', '--force',
        help='Overwrite',
        action='store_true'
    )

    parser.add_argument(
        '-o', '--output',
        help='Download as',
        default='.'
    )
    pkg_types = ', '.join(pkg_type.value for pkg_type in PackageType.__members__.values())
    parser.add_argument(
        '-t', '--package-type',
        help='Set the package type [{0}]. Defaults to downloading all '
             'package types available111'.format(pkg_types),
        action='append',
    )
    parser.set_defaults(main=main)


def main(args):
    aserver_api = get_server_api(args.token, args.site)
    username, notebook = parse(args.handle)
    username = username or aserver_api.user()['login']
    downloader = Downloader(aserver_api, username, notebook)
    packages_types = [
        PackageType(ty) for ty in args.package_type] if args.package_type else list(PackageType.__members__.values())

    try:
        download_files = downloader.list_download_files(packages_types, output=args.output, force=args.force)
        for download_file, download_dist in download_files.items():
            downloader.download(download_dist)
            logger.info("{} has been downloaded as {}".format(args.handle, download_file))
            if has_environment(download_file):
                logger.info("{} has an environment embedded.".format(download_file))
                logger.info("Run:")
                logger.info("    conda env create {}".format(download_file))
                logger.info("To install the environment in your system")
    except (errors.DestionationPathExists, errors.NotFound, errors.BinstarError, OSError) as err:
        logger.info(err)
