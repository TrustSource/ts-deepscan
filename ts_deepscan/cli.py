import json
import click
import pathlib

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from .client import DSScanner
from .scanner.Scan import Scan
from .scanner.Scanner import *
from .scanner.ParallelScanner import ParallelScanner
from .analyser import get_analysers

from ts_python_client.client import Client


@click.group()
def cli():
    pass


@cli.command()
@click.option('-o', '--output',
              type=click.Path(path_type=pathlib.Path),
              help='Output path for the results')
@click.option('-j', '--jobs',
              default=-1,
              help='Number of parallel jobs')
@click.option('--include-copyright',
              default=False,
              is_flag=True,
              help='Enables searching for copyright information in files')
@click.option('--filter-files',
              default=False,
              is_flag=True,
              help='Only scan files based on commonly used names (LICENSE, README, etc.) and extensions (source code files)')
@click.option('--pattern',
              multiple=True,
              default=[],
              help='Specify Unix style file name pattern')
@click.argument('path', type=click.Path(exists=True, path_type=pathlib.Path))
def scan(output: pathlib.Path,
         jobs: int,
         include_copyright: bool,
         filter_files: bool,
         pattern: List[str],
         path: pathlib.Path):

    options = AnalyserOptions(includeCopyright=include_copyright,
                              filterFiles=filter_files,
                              filePatterns=list(pattern))

    result, no_result, stats = execute(path, jobs, options)

    _scan = Scan(result=result,
                 no_result =no_result,
                 stats = stats, # prepare_stats(result, no_result, stats)
                 options=options)
    _scan.compute_licenses_compatibility()

    if output:
        with output.open('w') as fp:
            fp.write(json.dumps(_scan.to_dict(), indent=2))
    else:
        print(json.dumps(_scan.to_dict(), indent=2))



def execute(path: Path, jobs: int, options: AnalyserOptions):
    from typing import Optional
    from progress.bar import Bar

    scanner = ParallelScanner(jobs, [path], get_analysers(), options)

    no_result = []
    def onSuccess(p, r):
        if not r:
            no_result.append(p)

    scanner.onFileScanSuccess = onSuccess

    progress_bar: Optional[Bar] = None
    def onProgress(finishedTasks: int, totalTasks: int):
        nonlocal progress_bar
        if finishedTasks == 0:
            progress_bar = Bar('Scanning', max=totalTasks)
        elif progress_bar:
            progress_bar.next()

    scanner.onProgress = onProgress

    result = scanner.run()
    progress_bar.finish()

    return result, no_result, {
        'total': scanner.totalTasks,
        'finished': scanner.finishedTasks
    }


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



###########

@cli.command()
@click.option('--project-name',
              type=str,
              required=True,
              help='Project name')
@click.option('--module-name',
              type=str,
              required=True,
              help='Module name of the scan')
@click.option('--api-key',
              type=str,
              required=True,
              help='TrustSource API Key')
@click.option('--base-url',
              default='',
              help='TrustSource API base URL')
@click.option('--deepscan-base-url',
              default='',
              help='DeepScan API base URL')
@click.argument('path', type=click.Path(exists=True, path_type=pathlib.Path))
def upload(project_name: str,
           module_name: str,
           api_key: str,
           base_url: str,
           deepscan_base_url: str,
           path: pathlib.Path):

    with path.open('r') as fp:
        _scan = Scan.from_dict(json.loads(fp.read()))

    scanner = DSScanner(_scan, moduleName=module_name, deepscanBaseUrl=deepscan_base_url)
    tool = Client('ts-deepscan', scanner)

    tool.run(baseUrl=base_url,
             apiKey=api_key,
             projectName=project_name,
             skipTransfer=False)



