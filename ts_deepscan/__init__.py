# SPDX-FileCopyrightText: 2023 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import sys
import json
import requests
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import gzip

from .config import get_datasetdir

from .scanner import Scan
from .scanner.Scanner import *
from .scanner.ParallelScanner import ParallelScanner

from .analyser import FileAnalyser
from .analyser.Dataset import Dataset

from .analyser.CommentAnalyser import CommentAnalyser
from .analyser.LicenseAnalyser import LicenseAnalyser


def __load_spacy_models():
    import spacy

    if not spacy.util.is_package('en_core_web_sm'):
        spacy.cli.download('en_core_web_sm')
        print()

    if not spacy.util.is_package('en_core_web_sm'):
        print('Cannot download language model')
        exit(2)


def create_default_analysers(dataset: Dataset, include_copyright: bool = False, include_crypto: bool = False) -> List[FileAnalyser]:
    analysers = [LicenseAnalyser(dataset, include_copyright), CommentAnalyser(dataset, include_copyright)]
    if include_crypto:
        try:
            from .analyser.CryptoAnalyser import CryptoAnalyser
            analysers.append(CryptoAnalyser())
        except Exception as err:
            print('Crypto analyser error: ', err)
            pass

    return analysers


def create_scanner(jobs: int = -1,
                   include_copyright: bool = False,
                   include_crypto: bool = False,
                   ignore_pattern: tuple = tuple()) -> Scanner:

    if sys.platform == 'win32':
        # Do crypto analysis without multitasking due to spawn + native libs issues on Windows
        jobs = 1

    dataset = create_dataset()
    analysers = create_default_analysers(dataset, include_copyright, include_crypto)

    return ParallelScanner(num_jobs=jobs,
                           analysers=analysers,
                           ignore_patterns=list(ignore_pattern))


def create_dataset():
    path = get_datasetdir()

    dataset = Dataset(path)
    dataset.load()

    return dataset


def execute_scan(paths: [Path], _scanner: Scanner, title = '') -> Scan:
    from progress.bar import Bar

    no_result = []
    def onSuccess(p, r):
        if not r:
            no_result.append(p)

    _scanner.onFileScanSuccess = onSuccess

    progress_bar: Optional[Bar] = None
    def onProgress(finishedTasks: int, totalTasks: int):
        nonlocal progress_bar
        if finishedTasks == 0:
            bar_title = f"Scanning {title}" if title else "Scanning"
            progress_bar = Bar(bar_title, max=totalTasks)
        elif progress_bar:
            progress_bar.next()

    _scanner.onProgress = onProgress

    result = _scanner.run(paths)

    if progress_bar:
        progress_bar.finish()

    stats = {
        'total': _scanner.totalTasks,
        'finished': _scanner.finishedTasks
    }

    _scan = Scan(result=result,
                 no_result =no_result,
                 stats = stats, # prepare_stats(result, no_result, stats)
                 options=_scanner.options)

    _scan.compute_licenses_compatibility()

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



deepscanBaseUrl = 'https://api.prod.trustsource.io/deepscan'

__DIRECT_UPLOAD_SIZE_LIMIT = 500 * 1024 # 500KB: Upload limit without an intermediate storage

def upload_data(data: dict, module_name: str, api_key: str, base_url = deepscanBaseUrl) -> Optional[Tuple[str, str]]:
    params = {
        'module': module_name
    }

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'ts-deepscan/1.0.0',
        'x-api-key': api_key
    }

    data = bytes(json.dumps(data), 'utf-8')
    compressed = gzip.compress(data)

    if len(data) <= __DIRECT_UPLOAD_SIZE_LIMIT:
        headers['Content-Encoding'] = 'gzip'
        resp = requests.post(f'{base_url}/upload-results', data=compressed, headers=headers, params=params)
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
            return uid, url

    except ValueError as err:
        print('Cannot decode response')
        print(err)

    return None


def _upload_with_request(data: bytes, headers: dict, params: dict, base_url = deepscanBaseUrl) -> requests.Response:
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