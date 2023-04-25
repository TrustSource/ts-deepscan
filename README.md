![Supported Versions](https://img.shields.io/badge/Python-3.6,%203.7,%203.8,%203.9-blue) 
![License](https://img.shields.io/badge/License-Apache--2.0-green)

# TrustSource DeepScan 
Repository scanner for the identification of *_effective licenses and copyright information_*. 

## What it does? 
DeepScan takes the URL of a git repository as input, clones the content and scans all files contained (see below) for license indicators and copyright comments. All *findings* will be returned in a hirarchical structure (including references) and the cloned repo will be deleted afterwards. 

We provided also a hosted version with a nice UI, that you can find [here](https://deepscan.trustsource.io "Link to DeepScan Service"). The hosted version is available for free through the Web-UI. It is also part of the subscription based [TrustSource](https://app.trustsource.io)-Service. This version allows in addition the cloning and scanning of private repositories. It has been set up to support many and large repositories. If you are interested in using it from within your CI/CD pipeline, we offer API-subscriptions.

To learn more about TrustSource - the only process focussed Open Source Compliance tool, which supports all aspects of the open source compliance tool chain - visit our website at https://www.trustsource.io.

## What it covers? 
Currently, the tool searches all kind of source files for comments. It covers a wide range of programming languages:
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

In addition, it assesses all LICENSE, COPYING and README named files. Text, respectively comments in source files, will be analyzed for copyright statements and licenses will be verified against the original liecense text using a similarity analysis approach. The tool compiles results in a JSON file. 

**PLEASE NOTE: The tool will ignore all kind of image, audio or video files.**

## How it works? 
You may decide upon what to include in the scan. You may want to search for license indications only or also for copyright information. The latter will increase the operations time drastically. 
The scanning has several phases. It seeks for SPDX license identifiers as well as compares license texts using a similarity analysis.
For the copyright scaning it has several routines but mainly builds on [ScanCode](https://github.com/nexB/scancode-toolkit "ScanCode Repository") (credits to [Philippe](https://github.com/nexB/scancode-toolkit/commits?author=pombredanne])).

## Where to learn more? 
DeepScan is the CLI-version of the [TrustSource DeepScan](https://www.trustsource.io/deepscan "DeepScan Webservice UI") service. TrustSource DeepScan is a free repository scanning service operated by [TrustSource](https://www.trustsource.io "TrustSource Website"). To learn more about it and how it works, see the [TrustSource Knowledgebase](https://support.trustsource.io). It is the "Repo-Scanner" part of the OpenChain Reference Tooling. See [here](https://support.trustsource.io/hc/en-us/articles/360012782880-Architecture-Overview "Link to article") for a complete description of the reference model. 

# Getting started / set up
The tool is realized in Python 3, we recommend to provide at least Python 3.7. To install it you may use pip:
```
pip install ts-deepscan
```
Currently, we do not support any alterantive installations, but we are planning to provide homebrew shortly.
To execute a scan, make sure the machine you are using to perform the scan has access to the internet, so that deepscan will be able to laod the latest Update of license data. This requires https (443). We regularly update the license texts. To provide this service, we kindly thank the [SPDX](https://spdx.org)-team. They do the heavy lifting on updating the licenses. 
```
# clone a repo
git clone https://github.com/trustsource/ts-deepscan

# execute a scan
ts-deepscan scan -o results.json ./ts-deepscan
```
If you omit the -o parameter, the tool will use standard out as default. For further options please see the next section.
In the first run, it will download the license data from this repository. Occasionlaly we update the file. Original data is provided by SPDX org.

# TrustSource DeepScan CLI usage and configuration options
DeepScan may be used to scan a complete directory or a single file depending on the path argument.

## CLI help

To list all available commands:

```
ts-deepscan --help
```

To get help to particular commands:

```
ts-deepscan <COMMAND> --help
```

## Selecting the scan target
To scan a particular file:
```
ts-deepscan scan ./ts-deepscan/LICENSE
```
To scan a complete directory:
```
ts-deepscan scan ./ts-deepscan
```

## Switching copyright collection on/off
The default is to scan for license indicators only. If you also want to invest into the costly search for copyright infromation, you must inlcude the *--include-copyright* parameter, e.g.:  
```
ts-deepscan scan --include-copyright ./ts-deepscan
```

## Switching detection of used cryptographic algorithms on/off
If you want to turn on the search for used cryptographic algorithms in source code files (based on ScanOSS detection algorithms), you must inlcude the *--include-crypto* parameter, e.g.:  
```
ts-deepscan scan --include-crypto ./ts-deepscan
```

## Selecting the output target
Default output will be stdout (console). To write in a file instead, use the -o option, e.g.:
```
ts-deepscan scan --include-copyright -o result.json ./ts-deepscan
```

## Exclude files from analysis
If you want to exclude files from analysis while scanning directories, you can specify one or more ignore file patterns using the *--ignore-pattern* option, e.g. the following command 
```
ts-deepscan scan --ignore-pattern "*.pyc" -o result.json ./ts-deepscan
```
scans the directory 'ts-deepscan' and exludes all Python compiled files with an extension "pyc" from the analysis.  

## Number of parallel jobs
The default is to use the maximal number of availbale CPU cores (cpu_count - 1) on Unix based systems and one core on Windows (due to slow process forking), if you want to specify the number of parallel jobs manually, you can use *-j* option, e.g.

```
ts-deepscan scan -j 4 -o result.json ./ts-deepscan
```

## Uploading scan results
For uploading previously stored scan results (scan executed with the '-o' option) to the TrustSource app use the following command: 

```
ts-deepscan upload --project-name <YOUR_PROJECT_NAME> --module-name ts-deepscan --api-key <YOUR_API_KEY> result.json
```

Note: before uploading scan, a project has to be created in the TrustSource app as well as an API key has to be generated in the TrustSource Account settings  

# Next steps
On our roadmap we see two capabilities being of relevance:

### a) Identify license deltas
Given we identified a license text, with a similarity lower than 90%, it is possible that the original license text has been amended. Sometimes authors do add a clause or remove one. In a next version, we plan to outline these deltas. 

### b) Identify re-use of code
Currently, each file assessed is hashed, so that we do not need to assess the same file several times. This can be used to identify multiple appearances of the same file across different repositories. 

### c) Treatment of linked repositories
In GitHub and other git derivatives it is possible to link a repository into your repository. The current version is treating these repositories as local code, which leads to difficulties with direct links

In case you have specific need for any of the cases mentioned above, feel free to reach out and let us know about your case. If you have additional ideas, feel free to open a feature request in the issues section. 

# Contribution, Contact and Support
Feel free to reach out to the [TrustSource Team](https://support.trustsource.io/hc/en-us/requests/new "TrustSource Knowledgebase") by dropping us a message or providing [issues](/org/ts-deepscan/issues). We'ld love to hear your feedback to learn and improve.
Contributions are welcome. Just clone, create your branch and send a pull request. Please make sure to agree to the [contribution agreement](/org/ContributionAgreeemnt.md "Contribution Agreement") and the [coding guidelines](/org/CodingGuidelines.md "Coding Guidelines").

If you like the tool and want to support our further work, feel free to support us with donations or sign an API-usage agreement.
Thank you & best regards!
