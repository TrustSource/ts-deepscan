# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import os
import platform
import tempfile

from pathlib import Path


def get_tempdir() -> Path:
    return Path('/tmp') if platform.system() == 'Darwin' else Path(tempfile.gettempdir())


def get_datasetdir(createIfNotExist=True):
    dirpath = os.getenv('TS_DEEPSCAN_DATASET_DIR', None)
    dirpath = Path(dirpath) if dirpath else get_tempdir()/'ts-deepscan'

    if not dirpath.exists() and createIfNotExist:
        dirpath.mkdir(0o744, parents=True, exist_ok=True)

    return dirpath


