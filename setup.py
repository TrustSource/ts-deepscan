from setuptools import setup

setup(
    name='ts-deepscan',
    python_requires='>3.6',
    packages=[
        'ts_deepscan',
        'ts_deepscan.analyser',
        'ts_deepscan.commentparser',
        'ts_deepscan.scanner',
        'ts_deepscan.scancode',
        'ts_deepscan.scancode.cluecode',
    ],
    version='0.6.0',
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
        'nltk',
        'text-unidecode',
        'requests',
#        'osadl_matrix',
        'ts-python-client>=1.2.0'
    ],
    scripts=['ts-deepscan'],
    entry_points={
        'console_scripts': ['ts-deepscan=ts_deepscan.cli:main'],
    },
    include_package_data=True
)