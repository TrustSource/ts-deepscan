# SPDX-FileCopyrightText: 2023 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import sys
import json
import requests
import warnings
import typing as t
import gzip

from tqdm import tqdm
# noinspection PyProtectedMember
from dataclasses_json.core import _ExtendedEncoder

from .config import get_datasetdir

from .scanner import Scan, compute_summary
from .scanner.Scanner import *
from .scanner.PoolScanner import PoolScanner

from .analyser import FileAnalyser
from .analyser.Dataset import Dataset

from .analyser.CommentAnalyser import CommentAnalyser
from .analyser.LicenseAnalyser import LicenseAnalyser
from .analyser.ScanossAnalyser import ScanossAnalyser
from .analyser.YaraAnalyser import YaraAnalyser

warnings.filterwarnings("ignore", category=FutureWarning)


def __load_spacy_models():
    import spacy

    if not spacy.util.is_package('en_core_web_sm'):
        spacy.cli.download('en_core_web_sm')
        print()

    if not spacy.util.is_package('en_core_web_sm'):
        print('Cannot download language model')
        exit(2)


def create_default_analysers(dataset: Dataset,
                             timeout: int,
                             max_file_size: int,
                             include_copyright: bool,
                             include_crypto: bool) -> List[FileAnalyser]:
    analysers = [LicenseAnalyser(dataset, include_copyright,
                                 timeout=timeout,
                                 max_file_size=max_file_size),
                 CommentAnalyser(dataset, include_copyright,
                                 timeout=timeout,
                                 max_file_size=max_file_size)]

    if include_crypto:
        try:
            from .analyser.CryptoAnalyser import CryptoAnalyser
            analysers.append(
                CryptoAnalyser(timeout=timeout, max_file_size=max_file_size))
        except Exception as err:
            print('Crypto analyser error: ', err)
            pass

    return analysers


def create_scanner(jobs: int = -1,
                   timeout: int = FileAnalyser.DEFAULT_TIMEOUT,
                   max_file_size: int = FileAnalyser.MAX_FILE_SIZE,
                   include_copyright: bool = True,
                   include_crypto: bool = True,
                   include_scanoss_wfp: bool = False,
                   include_yara: bool = False,
                   yara_rules: t.Optional[Path] = None,
                   ignore_pattern: tuple = tuple(),
                   default_gitignores: Optional[List[Path]] = None,
                   dataset: Optional[Dataset] = None) -> Scanner:

    if sys.platform == 'win32' and include_crypto:
        if jobs > 1:
            print('Warning: parallel analysis is unavailable on Windows when \'include-crypto\' flag is enabled')

        # Do crypto analysis without multitasking due to spawn + native libs issues on Windows
        jobs = 1

    if not dataset:
        dataset = create_dataset()

    analysers = create_default_analysers(dataset,
                                         timeout=timeout,
                                         max_file_size=max_file_size,
                                         include_copyright=include_copyright,
                                         include_crypto=include_crypto)

    if include_scanoss_wfp:
        analysers.append(ScanossAnalyser(timeout=timeout))

    if include_yara:
        if yara_rules:
            analysers.append(YaraAnalyser(
                timeout=timeout,
                max_file_size=max_file_size,
                rules_path=yara_rules))
        else:
            print('Warning: YARA analyser was not enabled. Please provide a path to YARA rules')

    return PoolScanner(num_jobs=jobs,
                       task_timeout=timeout,
                       analysers=analysers,
                       ignore_patterns=list(ignore_pattern),
                       default_gitignores=default_gitignores)


def create_dataset() -> Dataset:
    path = get_datasetdir()

    dataset = Dataset(path)
    dataset.load()

    return dataset


def execute_scan(paths: [Path], _scanner: Scanner, title='') -> Scan:
    no_result = []
    progress_bar: Optional[tqdm] = None

    def onScanCompleted(p, r, errs):
        if not r:
            no_result.append(p)

    def onProgress(finished: int, total: int):
        nonlocal progress_bar
        with tqdm.get_lock():
            if progress_bar is None:
                progress_bar = tqdm(
                    desc=f"Scanning {title}" if title else "Scanning",
                    total=total,
                    miniters=1,
                    leave=False)
            #                    bar_format='{desc:<40}{percentage:3.0f}%|{bar:10}{r_bar}')
            else:
                progress_bar.update(finished - progress_bar.n)

    _scanner.onProgress = onProgress
    _scanner.onFileScanCompleted = onScanCompleted

    result = _scanner.run(paths)

    if progress_bar is not None:
        with tqdm.get_lock():
            progress_bar.close()

    stats = {
        'total': _scanner.totalTasks,
        'finished': _scanner.finishedTasks
    }

    _scan = Scan(result=result,
                 no_result=no_result,
                 stats=stats,  # prepare_stats(result, no_result, stats)
                 options=_scanner.options)

    compute_summary(_scan)
    return _scan


def prepare_stats(result, no_result, stats):
    copyrights = {}
    copyrights_info_count = 0

    files = list(result.keys())
    files += no_result

    for path, res in result.items():
        for com in res.get('comments', []):
            for cop in com.get('copyright', []):
                for h in cop.get('holders', []):
                    copyrights_info_count += 1
                    if h in copyrights:
                        copyrights[h].append(path)
                    else:
                        copyrights[h] = [path]
                    files.remove(path)

    stats['copyright_info'] = copyrights_info_count
    stats['no_copyright_info'] = len(files)

    stats['copyright'] = copyrights
    copyrights['no_copyright'] = files

    return stats


baseUrl = 'https://api.prod.trustsource.io/deepscan'

__DIRECT_UPLOAD_SIZE_LIMIT = 100 * 1024  # 100KB: Upload limit without an intermediate storage


def upload_scan(scan: Scan, module_name: str, api_key: str, base_url=baseUrl) -> bool:
    params = {
        'module': module_name
    }

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'ts-deepscan/1.0.0',
        'x-api-key': api_key
    }

    # noinspection PyUnresolvedReferences
    data = bytes(json.dumps(scan.to_dict(), cls=_ExtendedEncoder), 'utf-8')
    compressed = gzip.compress(data)

    if len(data) <= __DIRECT_UPLOAD_SIZE_LIMIT:
        headers['Content-Encoding'] = 'gzip'
        resp = requests.post(f'{base_url}/upload-results', data=compressed, headers=headers, params=params)

        if resp.status_code == 504:
            # Timeout, try to upload using intermediate S3 storage
            resp = _upload_with_request(compressed, headers=headers, params=params, base_url=base_url)
    else:
        resp = _upload_with_request(compressed, headers=headers, params=params, base_url=base_url)

    if resp.status_code not in range(200, 300):
        print(f'Status {resp.status_code}: {resp.text}')
        exit(2)

    try:
        resp = resp.json()

        uid = resp.get('uid', '')
        url = resp.get('url', '')

        if uid:
            scan.uid = uid
            scan.url = url

            return True

    except ValueError as err:
        print('Cannot decode response')
        print(err)

    return False


def _upload_with_request(data: bytes, headers: dict, params: dict, base_url=baseUrl) -> requests.Response:
    resp = requests.get(f'{base_url}/request-upload', headers=headers)

    if resp.status_code not in range(200, 300):
        print(f'Requesting upload failed. Code {resp.status_code}: {resp.text}')
        exit(2)

    resp = resp.json()

    if (upload_url := resp.get('upload_url', None)) and (uid := resp.get('uid', None)):
        resp = requests.put(upload_url, data=data)
        if resp.status_code not in range(200, 300):
            print(f'Storage upload failed. Code {resp.status_code}: {resp.text}')
            exit(2)

        return requests.post(f'{base_url}/upload-results', json={'uid': uid}, headers=headers, params=params)

    else:
        print('Requesting upload failed. No upload URL provided by the server')
        exit(2)
