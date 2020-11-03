# TrustSource DeepScan 
Repository scanner for the identification of licenses and copyright information. 

## What it does? 
DeepScan takes the URL of a git repository as input, clones the content and scans all files contained (see below) for license indicators and copyright comments. All findings will be returned in a hirarchical structure (including references) and the cloned repo will be deleted afterwards. 

We provided also a hosted version, that you can find [here](https://deepscan.trustsource.io "Link to DeepScan Service"). The hosted version is availble for free through the Web-UI. It is also part of the subscription based [TrustSource](https://app.trustsource.io)-Service. This version allows in addition the cloning and scanning of private repositories. 

To learn more about TrustSource - the only process focussed Open Source Compliance tool, which supports all aspects of the open source compliance tool chain - visit our website at https://www.trustsource.io.

## What it covers? 
Currently the tool searches all kind of source files for comments. It covers a wide range of programming languages:
* AppleScript
* Assembly
* Batch
* C
* Clif 
* Clojure 
* CMake 
* CSharp 
* Dart
* Elixir 
* Fortran 
* GLSLF
* Go
* Haskell 
* HTML
* Flex 
* Java 
* JavaScript 
* Kotlin 
* Lisp 
* Matlab 
* Markdown 
* MySQL 
* NinjaBuild 
* ObjectiveC 
* Perl 
* Python 
* R
* Ruby 
* Rust 
* Shader
* Shell 
* SQL 
* Swift 
* SWIG 
* TypeScript 
* Yacc 
* Yaml
In addition it assesses LICENSE, COPYING and README files. Text, repsectively comments in source files, will be analyzed for copyright statements and licenses will be verified against the original liecense texts using a similarity analysis approach. The tool compiles results in a JSON file. 

**PLEASE NOTE: The tool will ignore all kind of image, audio or video files.**

## How it works? 
You may decide upon what to include in the scan. You may want to search for license indications only or also for copyright information. The latter will increase the operations time drastically. 
The scanning has several phases. It seeks for SPDX license identifiers as well as compares license texts using a similarity analysis.
For the copyright scaning it has several routines but mainly builds on [ScanCode](https://github.com/nexB/scancode-toolkit "ScanCode Repository") (credits to [Philippe](https://github.com/nexB/scancode-toolkit/commits?author=pombredanne]))

## Where to learn more? 
DeepScan is the CLI-version of the [TrustSource DeepScan](https://www.trustsource.io/deepscan "DeepScan Webservice UI") service. TrustSource DeepScan is a free repository scanning service operated by [TrustSource](https://www.trustsource.io "TrustSource Website"). To learn more about it and how it works, see the [TrustSource Knowledgebase](https://support.trustsource.io). It is the "Repo-Scanner" part of the OpenChain Reference Tooling. See [here](https://support.trustsource.io/hc/en-us/articles/360012782880-Architecture-Overview "Link to article") for a complete description of the reference model. 

# Getting started / set up
The tool is realized in python 3, we recommend to provide at least python 3.6. To install it you may use pip:
```

```
pip install ts-deepscan




# TrustSource DeepScan CLI usage
(tbc)

# Contribution, Contact and Support
Feel free to reach out to the [TrustSource Team](https://support.trustsource.io/hc/en-us/requests/new "TrustSource Knowledgebase") by dropping us a message or providing [issues](/org/ts-deepscan/issues).
Contributions are welcome. Just clone, create your branch and send a pull request. Please make sure to agree to the [contribution agreement](/org/ContributionAgreeemnt.md "Contribution Agreement") and the [coding guidelines](/org/CodingGuidelines.md "Coding Guidelines").

If you like the tool and want to support our further work, feel free to ((DONATE)) or sign a API-usage agreement.
Thank you & best regards!