# SPDX-FileCopyrightText: 2023 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import json
import sys
import click
import pathlib
import typing as t
import shutil

from .scanner import Scan
from .analyser import FileAnalyser

from . import create_scanner, execute_scan, upload_scan, baseUrl


def main():
    width = shutil.get_terminal_size(fallback=(120, 24)).columns
    cli(max_content_width=width)


@click.group()
@click.version_option(package_name='ts-deepscan')
def cli():
    pass


@cli.command('scan')
@click.option('-j', '--jobs', default=-1 if sys.platform != 'win32' else 1,
              help='Number of parallel jobs')
@click.option('--timeout', default=FileAnalyser.DEFAULT_TIMEOUT, show_default=True, required=False,
              help='Timeout in seconds for each file')
@click.option('--max-file-size', default=FileAnalyser.MAX_FILE_SIZE, show_default=True, required=False,
              help='Max file size in bytes to be scanned')
@click.option('--include-copyright/--no-include-copyright', default=True, show_default=True,
              help='Enables searching for copyright information in source code files')
@click.option('--include-crypto/--no-include-crypto', default=True, show_default=True,
              help='Enables searching for used cryptographic algorithms in source code files')
@click.option('--include-scanoss-wfp/--no-include-scanoss-wfp', default=True, show_default=True,
              help='Enables computation of file fingerprints using SCANOSS')
@click.option('--include-yara/--no-include-yara', default=False, show_default=True,
              help='Enables YARA analyser')
@click.option('--yara-rules', type=click.Path(exists=True, path_type=pathlib.Path), required=False,
              help='Directory path containing YARA rules')
@click.option('--ignore-pattern', type=str, multiple=True, required=False,
              help='Unix filename pattern for files that has to be ignored during a scan')
@click.option('-o', '--output', 'output_path', type=click.Path(path_type=pathlib.Path), required=False,
              help='Output path for the scan')
@click.argument('paths', type=click.Path(exists=True, path_type=pathlib.Path), nargs=-1)
def scan(paths: tuple, output_path: t.Optional[pathlib.Path], *args, **kwargs):
    scanner = create_scanner(*args, **kwargs)
    s = execute_scan(list(paths), scanner)

    # noinspection PyUnresolvedReferences
    s_json = s.to_json()

    if output_path:
        with output_path.resolve().open('w') as fp:
            fp.write(s_json)
    else:
        print(s_json)


@cli.command('upload')
@click.option('--base-url', default=baseUrl,
              help='DeepScan API base URL')
@click.option('--api-key', type=str, required=True,
              help='TrustSource API Key')
@click.option('--module-name', type=str, required=True,
              help='Module name of the scan')
@click.argument('path', type=click.Path(exists=True, path_type=pathlib.Path))
def upload(path: pathlib.Path, module_name: str, api_key: str, base_url: str):
    with path.open('r') as fp:
        scan = Scan.from_json(fp.read())

    if upload_scan(scan, module_name, api_key, base_url):
        print("Transfer success!")
        if url := scan.url:
            print(f"Results are available at: {url}")
    else:
        print('Files scan was not uploaded correctly')
        exit(2)
