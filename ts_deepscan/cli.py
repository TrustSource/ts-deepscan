# SPDX-FileCopyrightText: 2023 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import json
import sys
import click
import pathlib

from typing import List

from .scanner import Scan
from .analyser import FileAnalyser

from . import create_scanner, execute_scan, upload_data, deepscanBaseUrl

from ts_python_client.cli import get_start_cmd, scan

start = get_start_cmd(version='2.2.0')


def main():
    start()


@click.option('-j', '--jobs',
              default=-1 if sys.platform != 'win32' else 1,  # Turn off multitasking due to the long spawn on Windows
              help='Number of parallel jobs')
@click.option('--timeout',
              default=FileAnalyser.DEFAULT_TIMEOUT, show_default=True,
              required=False,
              help='Timeout in seconds for each file')
@click.option('--include-copyright',
              default=False, show_default=True,
              is_flag=True,
              help='Enables searching for copyright information in source code files')
@click.option('--include-crypto',
              default=False, show_default=True,
              is_flag=True,
              help='Enables searching for used cryptographic algorithms in source code files')
@click.option('--ignore-pattern',
              type=str,
              multiple=True,
              required=False,
              help='Unix filename pattern for files that has to be ignored during a scan')
@scan.impl
def scan(paths: List[pathlib.Path], *args, **kwargs) -> Scan:
    scanner = create_scanner(*args, **kwargs)
    return execute_scan(paths, scanner)


@start.command
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
@click.argument('path', type=click.Path(exists=True, path_type=pathlib.Path))
def upload(module_name: str, api_key: str, base_url: str, path: pathlib.Path, ):
    with path.open('r') as fp:
        data = json.load(fp)

    if res := upload_data(data, module_name, api_key, base_url):
        print("Transfer success!")
        if url := res[1]:
            print(f"Results are available at: {url}")
    else:
        print('Files scan was not uploaded correctly')
        exit(2)
