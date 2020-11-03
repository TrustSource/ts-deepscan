import sys
import getopt
import json
import time

from .scanner.Scanner import *

from .analyser.Dataset import Dataset
from .analyser.SourcesAnalyser import SourcesAnalyser
from .analyser.LicenseAnalyser import LicenseAnalyser


def usage():
    print('usage: ts-deepscan <path> [-o filename] [--includeCopyrights] [--filterFiles]')


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:', ['--output', '--includeCopyright', '--filterFiles'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # Read input

    if len(args) != 1:
        usage()
        exit(2)

    output = None

    path = Path(args[0])
    options = AnalyserOptions()

    for opt, arg in opts:
        if opt in ['-o', '--output']:
            output = arg
        elif opt == '--includeCopyright':
            options.includeCopyright = True
        elif opt == '--filterFiles':
            options.filterFiles = True

    if not path.exists():
        print('Path {} does not exist'.format(str(path)))
        usage()
        exit(2)


    # Run scanner
    result = None

    if path.is_file():
        result = scan_file(path, options)
    elif path.is_dir():
        result = scan_folder(path, options)
    else:
        print('Path {} is not a file nor a directory'.format(str(path)))
        usage()
        exit(2)

    print()

    # Output result
    if not result:
        print('Nothing found')
        return

    if output:
        with open(output, 'w') as fp:
            fp.write(json.dumps(result))
    else:
        print(json.dumps(result, indent=2))



def scan_file(path, options):
    scanner = FileScanner(path, get_analysers(), options)
    print('Scanning... [1\\1]')
    return scanner.run()


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
    path = config.get_datasetdir()

    dataset = Dataset(path)

    print('Loading dataset...')
    dataset.load()

    return [LicenseAnalyser(dataset), SourcesAnalyser(dataset)]

