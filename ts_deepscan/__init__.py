# SPDX-FileCopyrightText: 2023 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import sys
import requests
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


from .scanner import Scan
from .scanner.Scanner import *
from .scanner.ParallelScanner import ParallelScanner
from .analyser import get_default_analysers


def create_scanner(jobs: int = -1,
                   include_copyright: bool = False,
                   include_crypto: bool = False,
                   filter_files: bool = False,
                   pattern: Optional[List[str]] = None) -> Scanner:

    pattern = [] if pattern is None else pattern
    opts = AnalyserOptions(includeCopyright=include_copyright,
                           filterFiles=filter_files,
                           filePatterns=pattern)

    analysers = get_default_analysers()

    if include_crypto:
        if sys.platform == 'win32':
            # Do crypto analysis without multitasking due to spawn + native libs issues on Windows
            jobs = 1

        try:
            from .analyser.CryptoAnalyser import CryptoAnalyser
            analysers.append(CryptoAnalyser())
        except Exception as err:
            print('Crypto analyser error: ', err)
            pass

    return ParallelScanner(jobs, analysers, opts)



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

def upload_data(data: dict, module_name: str, api_key: str, base_url = deepscanBaseUrl) -> Optional[Tuple[str, str]]:
    url = '{}/upload-results?module={}'.format(base_url, module_name)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'ts-deepscan/1.0.0',
        'x-api-key': api_key
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code not in range(200, 300):
        print('Status {}: {}'.format(response.status_code, response.text))
        exit(2)

    try:
        response = response.json()

        uid = response.get('uid', '')
        url = response.get('url', '')

        if uid:
            return uid, url

    except ValueError as err:
        print('Cannot decode response')
        print(err)

    return None