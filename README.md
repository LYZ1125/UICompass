# UICOMPASS: UI Manual Guided Mobile Task Automation via Adaptive Instruction Replanning

**This is the code repository for the paper  “UICOMPASS: UI Manual Guided Mobile Task Automation via Adaptive Instruction Replanning”**

# Introduction
The repository mainly consists of three parts:  

1. **uimanualgenerator** → The code section for generating the UI manual.
2. **taskexecutor** → The part for task execution.  
3. **experiment** → Experimental results.


##  UIManualGenerator

### How to run
1. Run the following command to generate the basic data.  
> python main.py
2. Run the following command to integrate it into the UI Manual.
> python UIManualGenerator.py


###  Dataset
apk_list is the list of application APKs, and app_project is the list of application source code.


### Existing result.
The **program_analysis_results** contains the basic data we’ve already generated (Method-level analysis results). It includes class-level information and method-level information.

The code_maps folder contains the UI manuals for various applications.










### Ennvironment:
| Package            | Version      |
|--------------------|--------------|
| annotated-types    | 0.7.0        |
| anyio              | 4.6.2.post1  |
| blinker            | 1.9.0        |
| cachetools         | 5.5.1        |
| certifi            | 2024.8.30    |
| click              | 8.1.7        |
| colorama           | 0.4.6        |
| distro             | 1.9.0        |
| et_xmlfile         | 2.0.0        |
| exceptiongroup     | 1.2.2        |
| Flask              | 3.1.0        |
| h11                | 0.14.0       |
| httpcore           | 1.0.7        |
| httpx              | 0.28.0       |
| idna               | 3.10         |
| importlib_metadata | 8.5.0        |
| itsdangerous       | 2.2.0        |
| Jinja2             | 3.1.4        |
| jiter              | 0.8.0        |
| MarkupSafe         | 3.0.2        |
| numpy              | 2.0.2        |
| openai             | 1.55.3       |
| openpyxl           | 3.1.5        |
| pandas             | 2.2.3        |
| pip                | 24.2         |
| pydantic           | 2.10.2       |
| pydantic_core      | 2.27.1       |
| PyJWT              | 2.8.0        |
| python-dateutil    | 2.9.0.post0  |
| pytz               | 2025.1       |
| setuptools         | 75.1.0       |
| six                | 1.17.0       |
| sniffio            | 1.3.1        |
| tqdm               | 4.67.1       |
| tree_sitter        | 0.20.1       |
| typing_extensions  | 4.12.2       |
| tzdata             | 2025.1       |
| Werkzeug           | 3.1.3        |
| wheel              | 0.44.0       |
| zhipuai            | 2.1.5.20250106|
| zipp               | 3.21.0       |





## TaskExecutor



> python run_command.py --port emulator-5554

Note: The default is emulator-5554.

Ennvironment:

| Package             | Version     |
|---------------------|-------------|
| adbutils            | 2.8.0       |
| aiohappyeyeballs    | 2.4.3       |
| aiohttp             | 3.10.10     |
| aiosignal           | 1.3.1       |
| annotated-types     | 0.7.0       |
| anyio               | 3.7.1       |
| apkutils2           | 1.0.0       |
| async-timeout       | 4.0.3       |
| attrs               | 24.2.0      |
| cached-property     | 1.5.2       |
| certifi             | 2024.8.30   |
| charset-normalizer  | 3.4.0       |
| cigam               | 0.0.3       |
| colorama            | 0.4.6       |
| contourpy           | 1.1.1       |
| cycler              | 0.12.1      |
| decorator           | 5.1.1       |
| Deprecated          | 1.2.14      |
| deprecation         | 2.1.0       |
| distro              | 1.9.0       |
| exceptiongroup      | 1.2.2       |
| filelock            | 3.16.1      |
| fonttools           | 4.55.3      |
| frozenlist          | 1.5.0       |
| h11                 | 0.14.0      |
| httpcore            | 1.0.6       |
| httpx               | 0.27.2      |
| idna                | 3.10        |
| importlib_resources | 6.4.5       |
| jiter               | 0.7.0       |
| kiwisolver          | 1.4.7       |
| logzero             | 1.7.0       |
| lxml                | 5.3.0       |
| matplotlib          | 3.7.5       |
| multidict           | 6.1.0       |
| numpy               | 1.24.4      |
| openai              | 1.55.3      |
| opencv-python       | 4.10.0.84   |
| packaging           | 24.2        |
| pillow              | 10.4.0      |
| pip                 | 24.2        |
| progress            | 1.6         |
| propcache           | 0.2.0       |
| py                  | 1.11.0      |
| pydantic            | 2.9.2       |
| pydantic_core       | 2.23.4      |
| pyelftools          | 0.31        |
| pyparsing           | 3.1.4       |
| python-dateutil     | 2.9.0.post0 |
| requests            | 2.32.3      |
| retry               | 0.9.2       |
| setuptools          | 75.1.0      |
| six                 | 1.16.0      |
| sniffio             | 1.3.1       |
| tenacity            | 8.2.3       |
| tqdm                | 4.67.0      |
| typing_extensions   | 4.12.2      |
| uiautomator2        | 2.16.25     |
| urllib3             | 2.2.3       |
| wheel               | 0.44.0      |
| whichcraft          | 0.6.1       |
| wrapt               | 1.16.0      |
| xmltodict           | 0.14.2      |
| yarl                | 1.15.2      |
| zipp                | 3.20.2      |





