# ts-deepscan
TS-DeepScan

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2025-02-25
### New Features
    * Add YARA analyser
    * Add SCANOSS analyser
    * Add a flag for the file size limit, to skip opening and scanning of large files
    * Add a multiprocessing.pool based scanner executing an analysis as a separate job
    * Switch setup configuration to the pyproject.toml
    * Update and pin package dependencies

## [2.2.0] - 2024-03-27
### New Features
    * Add timeout option to the file analysis

## [2.1.2] - 2024-02-19
### Fixes
    * Fix errors reporting occurring during file scans  

## [2.1.0] - 2024-01-22
### New Features
    * Add Scancode Toolkit (32.0.8) to the analysers 

## [2.0.7] - 2023-10-17
### Fixes
    * Fixed scan time initialization

## [2.0.6] - 2023-09-08
### Changed Features
    * Large files upload
    * Switched to the latest major version of the spaCy (3.x) library
    * Add support to scan archives
    * Reduce licenses dataset size

## [2.0.5] - 2023-05-25
### Changed Features
    * Update to the latest 'ts-python-client' (2.0.4)

## [2.0.4] - 2023-05-24 [DEPRECATED]
### Fixes
    * Fixed passing an API key to the header by results uploading

## [2.0.3] - 2023-05-03
### Changed Features
    * Update to the latest 'ts-python-client' to fix CLI option issues 

## [2.0.2] - 2023-04-04
### Changed Features
    * Minor bug fixes and improvements

## [2.0.1] - 2023-04-03
### New Features
    * Move text utilities to a separate package  

## [2.0.0] - 2023-03-13
### New Features
    * Switched to the latest major version of 'ts-python-client' (2.x)
    * Analysers refactoring
    * Simplify usage of the analysers in external tools as a library 

## [1.1.0] - 2023-02-16
### New features 
    * Analysis of the cryptographic algorithms usage in the source code using the ScanOSS Mining tool

### Changed Features
    * Minor bug fixes and improvements

## [1.0.3] - 2022-07-06

### Changed Features
    * Fix creation of worker processes on Windows (use "spawn")

## [1.0.2] - 2022-06-14

### Changed Features
    * Fix components key generation

## [1.0.1] - 2022-06-14

### Changed Features
    * Minor fixes

## [1.0.0] - 2022-06-13

### Changed Features
    * Create and upload a module based on the files scan to the TrustSource service
    * Use the root folder license as the license for the module's component
    * Provide separate commands for scanning and uploading results 
    * Add multiprocessing support ("-j N" option to specify number of parallel jobs) 
    * Add license compatibility checks

## [0.6.0] - 2022-06-08

### Changed Features
    * Add files filtering based on unix file name patterns
    * Upload module scans together with files scans to the TrustSource service  
