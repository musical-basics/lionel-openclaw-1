# DreamPlay Orders Into the System V1 — Tier 2 Claude Code Worker Prompt

You are the Tier 2 development worker for DreamPlay.

Repo:
`/home/openclaw/.openclaw/workspace/dreamplay-website-3`

## Required execution mode
You must use Claude Code for the substantive coding pass on this task.
Do not do the whole implementation purely by hand unless Claude Code is unavailable.

Claude Code launcher:
`/home/openclaw/.openclaw/workspace/scripts/claude-development.sh`

How to use Claude Code on this task:
1. Read the repo/context files listed below.
2. Build a strong high-level implementation brief for Claude Code.
3. Run Claude Code from the repo root with that brief.
4. Let Claude Code make the implementation changes.
5. Review the diff yourself, verify behavior, fix any gaps, and commit.
6. If Claude Code is unavailable, auth fails, or it produces bad changes, report the exact blocker or correct the issues before finishing.

Use Claude Code well:
- give it goals, constraints, business rules, target files, and acceptance criteria
- do not micromanage line by line
- prefer small, reviewable, robust changes
- make Claude inspect existing portal/auth code before changing anything

## Read these first
1. `/home/openclaw/.openclaw/workspace/specs/dreamplay-customer-portal-v1-tier1-spec.md`
2. `/home/openclaw/.openclaw/workspace/specs/dreamplay-orders-into-system-v1-tier1-spec.md`
3. `/home/openclaw/.openclaw/workspace/dreamplay-website-3/docs/REPO-CONTEXT.md`

## Canonical local order snapshot for V1
- `/home/openclaw/.openclaw/workspace/data/dreamplay/orders/imports/2026-04-16-shopify-export.csv`
- `/home/openclaw/.openclaw/workspace/data/dreamplay/orders/2026-04-16-orders-normalized.csv`
- `/home/openclaw/.openclaw/workspace/data/dreamplay/orders/2026-04-16-orders-summary.json`

## Task
Implement the missing V1 internal preorder order layer and wire it into the existing buyer portal so `/my-reservation` shows real imported order data for the logged-in buyer.

Important framing:
“Put these orders into the system” does not mean storing a CSV somewhere.
It means the website/backend can actually use the imported order snapshot as the operative order source for the buyer portal.

Use the imported local snapshot for V1.
Do not require live Shopify Admin API access for this version.

## Business rules you must preserve
1. `Total` is the actual amount the customer paid.
2. `Lineitem name` determines payment type.
3. Normalize payment type to:
   - `full_payment`
   - `deposit_50`
   - `waitlist_reservation`
4. Older order prices are not the current price sheet.
5. Portal data must be private to the logged-in buyer only.
6. Do not auto-refund in V1.
7. Do not implement automated upgrade repricing/payment in V1.
8. Keep DreamPlay One and DreamPlay Pro clearly distinct.
9. Aztec Gold and Nightmare Black remain Pro-only.
10. Use `docs/PRICING.md` as canonical current pricing reference, but buyer paid amount must come from imported order `Total`.

## V1 operating assumption
Show one primary preorder record per logged-in buyer.
Match by normalized email.
If multiple records match the same email, choose deterministically by:
1. preferring `full_payment` or `deposit_50` over `waitlist_reservation`
2. then newest order date
Preserve enough source traceability that this can be changed later.

## Inspect these existing areas before coding
- `src/app/(website-pages)/my-reservation/page.tsx`
- `src/app/(website-pages)/my-reservation/ReservationDecisionModule.tsx`
- `src/actions/reservation-actions.ts`
- `src/app/(website-pages)/vip/page.tsx`
- `src/lib/supabase/*`

## Implementation requirements
1. Add the smallest safe internal order data layer needed for V1.
2. Make imported preorder records usable inside the website/backend.
3. Link logged-in buyers to preorder records primarily by normalized email.
4. Update `/my-reservation` so matched buyers can see:
   - identity
   - preorder/order status
   - amount paid
   - payment type
   - current selected choice
   - existing recorded decision, if present
5. Keep the current Keep / Upgrade / Cancel flow, but attach it to real preorder records.
6. Keep Upgrade and Cancel as request/managed flows in V1, not automatic execution.
7. Prefer additive changes over replacing the existing reservation-decision system.
8. Do not build live Shopify sync, webhook ingestion, or customer-account sync in this pass.

## Minimum internal preorder model
- source order id / order name
- customer email
- customer name if available
- order date
- financial status
- fulfillment status
- `total_paid`
- `payment_type`
- current selected choice summary
- parsed product metadata where safely available
- import batch id
- raw source traceability

## Implementation shape
- create the leanest reasonable schema/data path needed
- create a minimal import path for the canonical local order snapshot
- wire portal reads to the internal preorder records
- attach existing decision capture to those records
- keep the solution production-minded, but lean

If the repo lacks migration/schema infrastructure:
- do the smallest reasonable thing
- add explicit SQL/setup artifacts and a short run note
- do not overengineer

## Deliverables
1. Code changes
2. Any schema/SQL/import script needed
3. A short implementation note covering:
   - files changed
   - data model added
   - matching rule used
   - how the import works
   - how `/my-reservation` now resolves and renders preorder data
4. Verification results for:
   - one full payment preorder
   - one 50% reservation preorder
   - privacy check that one buyer cannot see another buyer’s order
5. A git commit with the completed implementation

## Success criteria
- imported DreamPlay orders are usable inside the website/backend as real internal records
- a buyer can log in and be matched to their own preorder by email
- portal shows correct paid amount from `Total`
- portal shows correct payment type from `Lineitem name`
- portal shows a useful current choice summary
- Keep / Upgrade / Cancel are wired to a real preorder record
- no live Shopify dependency is required for V1

If blocked, stop and report the exact blocker clearly.
