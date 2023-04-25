# ts-deepscan
TS-DeepScan

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
