# V7 Intelligence & Delivery Studio

## Operator flow
1. Review new real requests in /delivery-studio.html. The inbox polls every 30 seconds only while open; acknowledge explicitly. Existing CRM and commerce continue to own customer information and financial truth.
2. After a quote is accepted, open a project, assign an accountable owner and send the generated private client link through an authorized channel. The link is a bearer credential; share privately. Rotate it to revoke prior access. It is stored hashed, not in logs or public URLs. Project and payment states are separate.
3. Record milestones and actual customer-visible evidence. Completion requires every recorded milestone to be complete with evidence. This is operator attestation, not independent customer acceptance. Do not mark delivery without real evidence.
4. Record public source URL, observation date, fact, interpretation, recommendation and confidence. Findings default to private until shared. Source URLs are not fetched or independently validated by this release. Do not record personal or sensitive client material in shared fields.
5. Client Studio presents only its own milestones, shared findings, invoice amounts and reconciliation status. It accepts feedback; there is no file upload or customer login beyond the private capability link. Existing quote page remains the payment route.

## Public assessment
English and Persian versions contain eight selectable business issues and transparent rule-based recommendations, not a numerical score or autonomous competitor audit. Optional submission uses the existing Request API; receipts indicate stored requests, not bookings or payments. No email/push provider configured. No ad spend or outreach from the runtime.

## Deployment and validation
Docker starts intelligence.py; existing volume and runtime settings preserved. Run all regression modules plus test_intelligence_v7. A staging/CI test uses isolated temporary DB and synthetic data, never production customer records or live Stripe transactions. External browser QA, source verification, external notification, scanner, domain and merchant/tax setup are distinct remaining work. Operator access uses existing Basic auth behind HTTPS. No claim of revenue or independent verification of customer deliverables.
