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
        "spacy~=3.6.0",
        "nltk~=3.9",
        "text-unidecode~=1.3",
        "requests~=2.32.3",
        "click==8.1.7",
        "osadl_matrix==2024.5.22.10535",
        "pyminr~=0.1.1",
        "scancode-toolkit~=32.3.2",
        "dataclasses-json~=0.6.7",
        "gitignore-parser~=0.1.11",
        "tqdm~=4.66.3",
        "scanoss~=1.19.4",
        'yara-python~=4.5.0'
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
