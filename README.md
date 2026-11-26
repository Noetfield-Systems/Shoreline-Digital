# Shoreline Digital — Commercial Execution V2.0
Independent business technology and digital growth partner. This is a locally tested release candidate, not a live deployment.

## Run
Python 3.11+; no runtime dependencies. Set a strong unique operator password in environment, then `python server.py`. Open `http://127.0.0.1:8080/` and `/operator` (username `operator`). `python test_runtime.py` uses an isolated temporary database. Original English and Persian HTML preserved with targeted changes. Campaign routes: `/competition-en.html`, `/visibility-en.html`, `/automation-en.html` and `-fa.html` equivalents. Add `?utm_source=telegram` etc. to attribute inbound requests.

## Deploy
Use a dedicated Shoreline project with HTTPS reverse proxy, persistent private disk (`SHORELINE_DB`), strong `SHORELINE_OPERATOR_PASSWORD`, `HOST=0.0.0.0`, platform `PORT`, backups, retention policy, monitoring, and public request smoke tests. The built-in HTTP server is intended for local evaluation; use a hardened HTTP service before internet exposure. Do not place the SQLite file in public storage. Operator inbox requires manual monitoring; email alerts not integrated. No Stripe, Interac, automatic booking, or payment processing. Operator deposit stage is only a manually recorded assertion with evidence; independently verify the transaction before delivery. No personal data or test database included.

## Next
Unify remaining legacy catalog prices and consultation copy with validated offers; test mobile browsers, accessibility, operational privacy and delivery; connect authorized independent merchant; publish public site; run organic outreach before paid tests. No actual ads published, no customers contacted, no revenue verified.

## Commercial V3.0
Run `python commerce.py` instead of `python server.py`. `/commerce` is the private revenue workspace and `/quote.html#TOKEN` the private bilingual proposal view. Existing routes remain. Run `python -m unittest -v test_runtime test_commerce`. Read `docs/QUOTE_TO_CASH.md` for configuration, verified vs attested revenue, evidence handling and remaining limitations. No live merchant, repository or public deployment has been established in this release. No customer records included. Use hardened HTTPS deployment and a dedicated persistent database; do not publish the local HTTP development server as-is.

## V5 Revenue Activation
Use `python growth.py`. New scoped offers at `/offers-en.html` and `/offers-fa.html`. See `docs/REVENUE_ACTIVATION_V5.md` for authorized merchant configuration, actual Stripe read-back and deployment limits. `python -m unittest -v test_runtime test_commerce test_growth test_revenue_v5` (local only). No live payment link or production deployment established by this release.
