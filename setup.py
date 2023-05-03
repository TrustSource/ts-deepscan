from setuptools import setup

setup(
    name='ts-deepscan',
    python_requires='>=3.8',
    packages=[
        'ts_deepscan',
        'ts_deepscan.analyser',
        'ts_deepscan.analyser.textutils',
        'ts_deepscan.commentparser',
        'ts_deepscan.scanner',
        'ts_deepscan.scancode',
        'ts_deepscan.scancode.cluecode'
    ],
    version='2.0.3',
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
        'progress',
        'osadl_matrix',
        'ts-python-client>=2.0.3',
        'pyminr>=0.1.0'
    ],
    scripts=['ts-deepscan'],
    entry_points={
        'console_scripts': ['ts-deepscan=ts_deepscan.cli:main'],
    },
    setup_requires=[
        'wheel'
    ],
    include_package_data = True,
)