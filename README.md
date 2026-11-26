# Shoreline Digital

Intelligence. Technology. Growth.

Business Intelligence, Digital Growth & Technology Solutions — Metro Vancouver, Canada. English and Persian.

Founder-authorized commercial brand of Noetfield Systems Inc.; separate operational records and revenue attribution. This repository is being initialized from the locally tested Shoreline V5 revenue activation release. No live website, payment link, or collected revenue is represented by this initialization.

## Release import
The complete local release is `shoreline-revenue-activation-v5.zip`. It contains Python application source, bilingual public pages, operator and growth workspaces, test suites, documentation, marketing data and creative assets. Import the extracted files into this repository; do not commit `.env`, runtime databases, credentials or private customer records.

After full import, run `python -m unittest -v test_runtime test_commerce test_growth test_revenue_v5` and start locally with `python growth.py`. Production deployment requires persistent private storage, HTTPS, operator credentials, and merchant configuration.

**Import status: partial until all source files are present and verified.**
