# V6 — Commercial launch and premium studio

V5 endpoints and all legacy campaign, intelligence and industry routes retained. New homepage `/` (`/studio-en.html`), RTL `/studio-fa.html`, theme preference, responsive navigation and direct intake with attribution. No fabricated testimonials or portfolio. Home form confirms only successful persisted request, not booking or payment. Services C01–C08 route through the existing CRM. The studio visual theme is new; legacy detail pages remain to be visually unified.

Production: run `python production.py` behind Railway managed TLS. Attach persistent `/data` volume and configure `SHORELINE_OPERATOR_PASSWORD` (unique 20+ chars), `SHORELINE_PUBLIC_URL` (HTTPS origin), `SHORELINE_DB=/data/shoreline.sqlite3`. Bounded concurrency and socket timeout, no request logs, JSON-only writes and origin checks when configured. No secrets in git. Backup/restore, operator notification and production load validation still required. Existing quote flows remain available; live Stripe tax status and key must be configured by authorized merchant; no test charges in live. No ad spend or outreach claimed. No automatic booking availability claim.

Operator: `/operator`, `/commerce`, `/growth`. Review new requests promptly, confirm scope, issue quote, accept, reconcile payment. Do not count research or test leads as real sales.
