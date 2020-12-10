# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import time
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

from .scanner.Scanner import *

from .analyser.Dataset import Dataset
from .analyser.SourcesAnalyser import SourcesAnalyser
from .analyser.LicenseAnalyser import LicenseAnalyser

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("path", help="File or directory to be scanned")

    parser.add_argument("-o", "--output", help="Store results to the OUTPUT in JSON format")

    parser.add_argument("--includeCopyright",
                        help="Enables searching for copyright information in files",
                        action="store_true")

    parser.add_argument("--filterFiles",
                        help="Only scan files based on commonly used names (LICENSE, README, etc.) and extensions (source code fies)",
                        action="store_true")

    args = parser.parse_args()

    path = Path(args.path)
    options = AnalyserOptions(includeCopyright=args.includeCopyright,
                              filterFiles=args.filterFiles)



    if not path.exists():
        print('Error: path {} does not exist'.format(str(path)))
        exit(2)


    # Run scanner
    result = None

    if path.is_file():
        result = scan_file(path, options)
    elif path.is_dir():
        result = scan_folder(path, options)
    else:
        print('Error: path {} is not a file nor a directory'.format(str(path)))
        exit(2)

    print()

    # Output result
    if not result:
        print('Nothing found')
        return

    if args.output:
        with open(args.output, 'w') as fp:
            fp.write(json.dumps(result))
    else:
        print(json.dumps(result, indent=2), )



def scan_file(path, options):
    scanner = FileScanner(path, get_analysers(), options)
    print('Scanning... [1\\1]')
    result = scanner.run()
    return list(result.values())[0] if result else None


def scan_folder(path, options):
    scanner = FolderScanner(path, get_analysers(), options)
    scan_finished = False

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
    return result


def get_analysers():
    import spacy

    path = config.get_datasetdir()
    dataset = Dataset(path)

    if not spacy.util.is_package('en_core_web_sm'):
        spacy.cli.download('en_core_web_sm');
        print()

    if not spacy.util.is_package('en_core_web_sm'):
        print('Cannot download language model')
        exit(2)

    print('Loading dataset...')
    dataset.load()

    return [LicenseAnalyser(dataset), SourcesAnalyser(dataset)]

