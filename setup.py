from setuptools import setup

setup(
    name='ts-deepscan',
    python_requires='>3.8',
    packages=[
        'ts_deepscan',
        'ts_deepscan.analyser',
        'ts_deepscan.commentparser',
        'ts_deepscan.scanner',
        'ts_deepscan.scancode',
        'ts_deepscan.scancode.cluecode',
    ],
    version='0.1',
    description='Repository scanner for the identification of effective licenses and copyright information.',
    author='EACG GmbH',
    license='Apache 2.0',
    url='https://github.com/TrustSource/ts-deepscan.git',
    download_url='',
    keywords=['DeepScan', 'TrustSource'],
    classifiers=[],
    install_requires=[
        'six',
        'spacy>=2.2.0,<3.0.0',
        'en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.3.0/en_core_web_sm-2.3.0.tar.gz',
        'nltk',
        'text-unidecode'
    ],
    scripts=['ts-deepscan'],
    entry_points={
        'console_scripts': ['ts-deepscan=ts_deepscan.cli:main'],
    },
    include_package_data=True
)