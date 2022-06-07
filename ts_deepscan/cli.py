# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0


import json
import time
import argparse

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from ts_python_client.client import Client

from .client import DSScanner
from .scanner.Scan import Scan
from .scanner.Scanner import *

from .analyser.Dataset import Dataset
from .analyser.SourcesAnalyser import SourcesAnalyser
from .analyser.LicenseAnalyser import LicenseAnalyser

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("path", help="File or directory to be scanned", nargs='+')

    parser.add_argument("-o", "--output", help="Store results to the OUTPUT in JSON format")

    parser.add_argument("--printStats",
                        help = "Print statistics",
                        action="store_true")

    parser.add_argument("--outputStats", help="Store statistics to the OUTPUTSTATS in JSON format")

    parser.add_argument("--includeCopyright",
                        help="Enables searching for copyright information in files",
                        action="store_true")

    parser.add_argument("--filterFiles",
                        help="Only scan files based on commonly used names (LICENSE, README, etc.) and extensions (source code files)",
                        action="store_true")

    parser.add_argument("--pattern",
                        help="Specify Unix style file name pattern",
                        action='append')

    parser.add_argument("--upload",
                        help="Upload to the TrustSource service",
                        action="store_true")

    parser.add_argument("--projectName", help="Project name")

    parser.add_argument("--moduleName", help="Module name of the scan")

    parser.add_argument("--apiKey", help="Upload to the TrustSource service")

    parser.add_argument("--baseUrl", help="DeepScan service base URL", )

    parser.add_argument("--deepscanBaseUrl", help="TrustSource service base URL", )

    args = parser.parse_args()

    options = AnalyserOptions(includeCopyright=args.includeCopyright,
                              filterFiles=args.filterFiles,
                              filePatterns=args.pattern)


    result, files, stats = execute([Path(p) for p in args.path], options)

    if not result:
        print('Nothing found')

    elif args.upload:
        scan = Scan(options=options)

        scan.result = result
        scan.stats = stats

        scanner = DSScanner(scan, moduleName=args.moduleName, deepscanBaseUrl=args.deepscanBaseUrl)
        tool = Client('ts-deepscan', scanner)

        tool.run(baseUrl=args.baseUrl,
                 apiKey=args.apiKey,
                 projectName=args.projectName,
                 skipTransfer=False)


    elif args.output:
        with open(args.output, 'w') as fp:
            fp.write(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))

    if args.printStats or args.outputStats:
        stats = prepare_stats(result, files, stats)
        stats = json.dumps(stats, indent=2)

        if args.printStats:
            print(stats)
        if args.outputStats:
            with open(args.outputStats, 'w') as fp:
                fp.write(stats)



def execute(paths: List[Path], options):
    scanner = FSScanner(paths, get_analysers(), options)

    scan_finished = False
    scanned_files = []

    scanner.onFileScanDone = lambda path: scanned_files.append(path)

    def print_progress(final=False):
        print('\rScanning... [{}\{}]'.format(scanner.finishedTasks, scanner.totalTasks), end='')
        if final: print()

    def update_progress():
        while not scan_finished:
            print_progress()
            time.sleep(2)

    progress = threading.Thread(target=update_progress)
    progress.start()

    result = scanner.run()

    scan_finished = True
    progress.join()

    print_progress(final=True)

    return result, scanned_files, {
        'total': scanner.totalTasks,
        'finished': scanner.finishedTasks
    }


def prepare_stats(result, files, stats):
    copyrights = {}
    copyrights_info_count = 0

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



def get_analysers():
    import spacy

    path = config.get_datasetdir()
    dataset = Dataset(path)

    if not spacy.util.is_package('en_core_web_sm'):
        spacy.cli.download('en_core_web_sm')
        print()

    if not spacy.util.is_package('en_core_web_sm'):
        print('Cannot download language model')
        exit(2)

    print('Loading dataset...')
    dataset.load()

    return [LicenseAnalyser(dataset), SourcesAnalyser(dataset)]



