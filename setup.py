from setuptools import setup, find_packages

setup(
    name='ts-deepscan',
    python_requires='>=3.8',
    packages=find_packages(),
    version='2.3.0',
    description='Repository scanner for the identification of effective licenses and copyright information.',
    author='EACG GmbH',
    license='Apache 2.0',
    url='https://github.com/TrustSource/ts-deepscan.git',
    download_url='',
    keywords=['DeepScan', 'TrustSource'],
    classifiers=[],
    install_requires=[
        'six',
        'spacy==3.7.4',
        "nltk==3.9",
        'text-unidecode',
        'requests==2.32.3',
        'osadl_matrix',
        'pyminr>=0.1.1',
        'scancode-toolkit-mini==32.3.0',
        'dataclasses-json',
        'gitignore-parser==0.1.11',
        "tqdm==4.66.3",
        "scanoss==1.19.4"
    ],
    scripts=['ts-deepscan'],
    entry_points={
        'console_scripts': ['ts-deepscan=ts_deepscan.cli:main'],
    },
    setup_requires=[
        'wheel'
    ],
    include_package_data=True,
)
