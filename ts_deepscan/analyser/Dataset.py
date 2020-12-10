# SPDX-FileCopyrightText: 2020 EACG GmbH
#
# SPDX-License-Identifier: Apache-2.0

import json
import shutil

from . import textutils

from pathlib import Path

class Dataset(object):
    def __init__(self, path: Path):
        self.__path = path
        self.__datasetpath = self.__path / 'dataset.json'

        self.__data = None
        self.__score_threshold = 0.8


    @property
    def data(self):
        return self.__data


    def preload(self, rebuildcache=False):
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


    def load(self, rebuildcache=False):
        if not self.__data:
            self.preload(rebuildcache)

        for _, val in self.__data.items():
            docpath = val['path']
            doc = textutils.create_doc()
            doc.from_disk(docpath)
            val['doc'] = doc



    def find_match(self, text):
        if not self.__data:
            raise Exception('Dataset is not loaded.')

        doc = textutils.create_doc(text)
        if not doc:
            return None, None

        hsh = textutils.compute_hash(doc)

        # Compare hashes
        for key, val in self.__data.items():
            if hsh == val['hash']:
                return key, 1.0


        lic = None
        score = 0.0

        # Compute similarity scores
        for key, val in self.__data.items():
            doc2 = val['doc']
            similarity = textutils.compute_similarity(doc, doc2)
            if similarity > score:
                score = similarity
                lic = key

        if score >= self.__score_threshold:
            return lic, score
        else:
            return None, None


    def _build(self):
        data = self._build_data()
        with open(self.__datasetpath, 'w') as fp:
            json.dump(data, fp)

        return data


    def _build_data(self):
        data = {}
        lics = Path(__file__).parent / 'licenses.json'

        with lics.open('r') as fp:
            licenses = json.load(fp)

            for key, lic in licenses.items():
                text = lic.get('text', None)
                if text:
                    data[key] = self._build_entry(key, text)
                    data[key]['name'] = lic.get('name', '')
                    data[key]['aliases'] = lic.get('aliases', [])

            return data


    def _build_entry(self, key, text):
        docpath = self.__path / '{}.bin'.format(key)

        doc = textutils.create_doc(text)
        doc.to_disk(docpath)

        return {
            'path': str(docpath),
            'hash': textutils.compute_hash(doc)
        }