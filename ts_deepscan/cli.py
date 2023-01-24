# SPDX-FileCopyrightText: 2023 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import sys
import click
import pathlib

from .scanner import Scan
from . import create_scanner, execute_scan, upload_data, deepscanBaseUrl

from ts_python_client.cli import start, scan, upload


def main():
    start()




@click.option('-j', '--jobs',
              default=-1 if sys.platform != 'win32' else 1, # Turn off multitasking due to the long spawn on Windows
              help='Number of parallel jobs')
@click.option('--include-copyright',
              default=False,
              is_flag=True,
              help='Enables searching for copyright information in source code files')
@click.option('--include-crypto',
              default=False,
              is_flag=True,
              help='Enables searching for used cryptographic algorithms in source code files')
@click.option('--filter-files',
              default=False,
              is_flag=True,
              help='Only scan files based on commonly used names (LICENSE, README, etc.) and extensions (source code files)')
@click.option('--pattern',
              multiple=True,
              default=[],
              help='Specify Unix style file name pattern')
@scan.impl
def scan(path: pathlib.Path, *args, **kwargs) -> Scan:
    scanner = create_scanner(*args, **kwargs)
    return execute_scan([path], scanner)






@click.option('--module-name',
              type=str,
              required=True,
              help='Module name of the scan')
@click.option('--api-key',
              type=str,
              required=True,
              help='TrustSource API Key')
@click.option('--base-url',
              default=deepscanBaseUrl,
              help='DeepScan API base URL')
@upload.override
def upload(data: dict, module_name: str, api_key: str, base_url: str):
    if res := upload_data(data, api_key, module_name, base_url):
        print("Transfer success!")
        if url := res[1]:
            print(f"Results are available at: {url}")
    else:
        print('Files scan was not uploaded correctly')
        exit(2)