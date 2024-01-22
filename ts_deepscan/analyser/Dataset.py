# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0
import json
import shutil
import typing as t

from pathlib import Path


class Dataset(object):
    def __init__(self, path: Path):
        self.__path = path
        self.__datasetpath = self.__path / 'dataset.json'

        self.__data = None

    @property
    def _licenses(self) -> t.Iterable[t.Tuple[str, dict]]:
        lics = Path(__file__).parent / 'licenses.json'
        with lics.open('r') as fp:
            licenses = json.load(fp)
            return licenses.items()

    @property
    def data(self):
        if not self.__data:
            raise Exception('Dataset is not loaded.')

        return self.__data

    def load(self, rebuildcache=False):
        path = self.__path
        datasetpath = self.__datasetpath

        if path.is_file():
            raise Exception('Cannot build dataset. {} is a file.'.format(path))

        if rebuildcache and path.exists():
            shutil.rmtree(path)

        if not path.exists():
            path.mkdir(0o744)
            rebuildcache = True

        if not rebuildcache and not datasetpath.exists():
            rebuildcache = True

        if rebuildcache:
            self.__data = self._build()

        if not self.__data:
            with open(datasetpath, 'r') as fp:
                self.__data = json.load(fp)

    def _build(self):
        data = self._build_data()
        with open(self.__datasetpath, 'w') as fp:
            json.dump(data, fp)

        return data

    def _build_data(self):
        data = {}

        for key, lic in self._licenses:
            text = lic.get('text', None)
            if text:
                data[key] = _build_entry(text)
                data[key]['name'] = lic.get('name', '')
                data[key]['aliases'] = lic.get('aliases', [])

        return data


def _build_entry(text):
    from .textutils import create_doc, compute_hash, similarity_tokens_from_doc
    #       docpath = self.__path / '{}.bin'.format(key)

    doc = create_doc(text)
    #        doc.to_disk(docpath)

    return {
        # 'path': str(docpath),
        'hash': compute_hash(doc),
        'orths': [tok.orth for tok in similarity_tokens_from_doc(doc)]
    }
