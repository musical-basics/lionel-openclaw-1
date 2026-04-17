# DreamPlay Orders Into the System V1 — Tier 1 Business Spec

## Goal
Turn the imported DreamPlay order export into a real internal order source the website can use.

This does **not** mean merely storing a CSV in the workspace.
It means the DreamPlay website/backend can use the imported orders to:
- identify preorder buyers
- show each buyer their own order status in the portal
- show how much they actually paid
- show their current selected choice
- support Keep / Upgrade / Cancel flows against that order record

## What Lionel meant by "put these orders into the system"
Business meaning:
- take the provided order dataset and make it usable inside the DreamPlay website stack
- do not depend on live Shopify access for V1
- preserve the business meaning of each order, not just raw rows
- make the data queryable by buyer account and portal flow

## V1 Source of Truth
For V1, the canonical order snapshot is the local imported dataset:
- `data/dreamplay/orders/imports/2026-04-16-shopify-export.csv`
- `data/dreamplay/orders/2026-04-16-orders-normalized.csv`
- `data/dreamplay/orders/2026-04-16-orders-summary.json`

Tier 1 recommendation:
- use this imported dataset as the operative source of truth for the portal until live Shopify sync is explicitly added
- design the internal order model so a future Shopify sync can replace the import source later without changing the portal contract

## Core Business Rules
1. `Total` is the amount the customer actually paid.
2. `Lineitem name` determines whether the order was:
   - a full payment
   - a 50% reservation / deposit
   - a waitlist-style reservation
3. Older order prices must **not** be treated as the current public price sheet.
4. The portal should show what this customer paid, not expose cross-customer pricing comparisons.
5. Order data shown in the portal must be private to the logged-in buyer.

## Recommended V1 System Design
Because `dreamplay-website-3` already uses Supabase for auth and buyer portal behavior, the clean V1 interpretation of "the system" is:
- Supabase-backed internal order records
- linked to the website's auth/buyer experience
- populated from the imported local order snapshot

In other words:
- local CSV = canonical import input
- Supabase/internal order table(s) = website-usable system of record for the portal
- `/my-reservation` = customer-facing surface

## Minimum Internal Order Model
V1 should create a normalized preorder record for each relevant order, with enough data to drive the portal.

### Required fields
At minimum, each preorder record should preserve:
- source order id / order name
- customer email
- customer name if available
- order date
- financial status
- fulfillment status
- `total_paid`
- `payment_type` derived from `Lineitem name`
- product snapshot / selected choice summary
- any useful size / finish / bundle metadata that can be parsed safely
- import batch identifier
- raw source reference for audit/debugging

### Recommended normalized fields
Use clean internal values where possible, such as:
- `full_payment`
- `deposit_50`
- `waitlist_reservation`

And portal-facing product fields such as:
- product family
- package type
- key size
- finish
- selected choice label

## Buyer Account Linking
V1 should link imported preorder records to website users primarily by normalized email.

Practical interpretation:
- buyer login identity comes from Supabase auth
- imported order email is the first-pass matching key
- if a logged-in buyer email matches an imported preorder email, the portal can load that preorder record

This is the missing bridge between:
- current Supabase auth / buyer gating
- and the real preorder data Lionel wants buyers to see

## Portal Outcome Required
Once the orders are "in the system," the `/my-reservation` portal should be able to show, per buyer:
- preorder/order status
- amount paid
- payment type
- current selected choice
- current recorded decision state if one exists

That means the reservation-decision system should sit on top of real internal preorder records, not float separately from them.

## Explicit Non-Goals for V1
Do **not** require these for the first useful version:
- live Shopify Admin API sync
- automatic refunds
- automatic upgrade repricing/payment collection
- exposing historical cross-customer pricing
- rebuilding the whole customer account architecture

## Acceptance Criteria
1. The imported DreamPlay orders are available inside the website/backend as queryable internal records.
2. A buyer can log in and be matched to their own preorder by email.
3. The portal can show the correct amount paid using `Total`.
4. The portal can distinguish full payment vs 50% reservation vs waitlist-style reservation using `Lineitem name`.
5. The portal can show a buyer-facing current choice summary based on the imported order data.
6. The current Keep / Upgrade / Cancel flow can be attached to a real preorder record.
7. The system works without live Shopify access.
8. The data model is future-safe enough that live Shopify sync can be added later without redefining portal semantics.

## Tier 1 Recommendation to Tier 2
Implement this as a two-layer system:

### Layer 1 — Order ingest / normalization
- take the canonical imported order snapshot
- load it into website-usable internal records
- preserve source traceability

### Layer 2 — Buyer portal consumption
- resolve logged-in buyer to preorder record by email
- render order/payment/selection data in `/my-reservation`
- attach existing decision capture to that record

## Open Questions
1. Should V1 support exactly one active preorder record per buyer in the portal, or handle multiple orders visibly?
2. If a buyer has multiple historical rows, what is the rule for the primary displayed record?
3. Which exact product-choice fields are already parseable from the current export versus needing manual cleanup?
4. When live Shopify sync is added later, should imported V1 records remain the fallback source if Shopify is unavailable?
