# TrustSource DeepScan 
Repository scanner for identification of licenses and copyright information. 

## What it does? 
DeepScan takes the URL of a git repository as input, clones the content and scans all files contained (see below) for license indicators and copyright comments. All findings will be returned in a hirarchical structure (including references) and the cloned repo will be deleted afterwards. 

Find [here|https://deepscan.trustsource.io] a free hosted version of the tool.

## What it covers? 
Currently the tool searches all kind of source files for comments. It covers a wide range of programming languages:
(...)
In addition it assesses LICENSE, COPYING and README files.

PLEASE NOTE: The tool will ignore all kind of image, audio or video files. 

## How it works? 
You may decide upon what to include in the scan. You may want to search for license indications only or also for copyright information. The latter will increase the operations time drastically. 
The scanning has several phases. It seeks for SPDX license identifiers as well as compares license texts using a similarity analysis.
For the copyright scaning it has several private routines but mainly builds on [ScanCode|https://github.com/nexB/scancode-toolkit] (credits to [Philippe|https://github.com/nexB/scancode-toolkit/commits?author=pombredanne])

## Where to learn more? 
DeepScan is the CLI-version of the [TrustSource DeepScan|https://www.trustsource.io/deepscan] service. TrustSource DeepScan is a free repository scanning service operated by [TrustSource|https://www.trustsource.io]. To learn more about it and how it works, see the [TrustSource Knowledgebase|https://support.trustsource.io]. It is the "Repo-Scanner" part of the OpenChain Reference Tooling. See [here|https://support.trustsource.io/hc/en-us/articles/360012782880-Architecture-Overview] for a complete description of the reference model. 

# TrustSource DeepScan CLI usage
(tbc)

# Contribution, Contact and Support
Feel free to reach out to the [TrustSource Team|https://support.trustsource.io] by dropping us an email or providing [issues|https://github.com/TrustSource/ts-deepscan/issues].
Contributions are welcome. Just clone, create your branch and send a pull request. Please make sure to agree to the [contribution agreement](/org/ContributionAgreeemnt.md "Contribution Agreement") and the [coding guidelines](/org/CodingGuidelines.md "Coding Guidelines").

If you like the tool and want to support our further work, feel free to ((DONATE)) or sign a API-usage agreement.
Thank you & best regards!
