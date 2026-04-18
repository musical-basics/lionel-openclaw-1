# DreamPlay Customer Portal V1 — Tier 1 Business Spec

## Goal
Preorder buyers need a customer portal where they can log in, see their preorder status and current selection, and choose one of three next actions:
- Keep
- Upgrade
- Cancel

This is the highest current DreamPlay product priority.

## Business Context
- DreamPlay preorder buyers are high-trust customers who already paid for a product that is delayed.
- The portal must reduce uncertainty, reduce manual back-and-forth, and give customers a clear next step.
- Voice must stay warm, professional, musician-first, and must not overpromise delivery timelines.

## Data / Business Rules
- Shopify order data is the source of truth for live customer order records.
- For payment interpretation, `Total` is the amount the customer actually paid.
- `Lineitem name` determines whether the customer paid a 50% reservation or fully paid.
- Older order amounts must not be treated as the current price sheet because DreamPlay pricing has increased.

## Portal Experience
When a preorder customer logs in, they should see:
1. Their name / account identity
2. Their preorder status
3. The amount they paid
4. Their current selected product choice
   - Example dimensions: model, size, finish, bundle/keyboard-only if applicable
5. A clear explanation of the three next actions:
   - Keep my current choice
   - Upgrade my order
   - Cancel my preorder

## Required Actions

### 1. Keep
Business outcome:
- The customer confirms they want to keep their current preorder choice.

Expected behavior:
- Button is wired and works.
- Customer sees a clear success state.
- Their confirmation is stored so DreamPlay can see that they want to keep their current selection.

### 2. Upgrade
Business outcome:
- The customer can signal they want to upgrade from their current selection.

Expected behavior:
- Button is wired and works.
- Customer is taken into an upgrade request flow or upgrade selection flow.
- DreamPlay can see which customer requested an upgrade and from which current selection.

Tier 1 recommendation for V1:
- Treat this as a request / managed flow first, not a fully automatic pricing or payment change, unless Lionel explicitly approves automated pricing behavior.

### 3. Cancel
Business outcome:
- The customer can signal they want to cancel their preorder.

Expected behavior:
- Button is wired and works.
- Customer is taken into a cancellation request / confirmation flow.
- DreamPlay can clearly see which customer requested cancellation.

Tier 1 recommendation for V1:
- Do not auto-refund in V1. Refunds must be escalated to Lionel.

## Important Business Constraints
- Refunds, pricing changes, customer complaints, public delivery timeline statements, and manufacturing decisions must be escalated to Lionel.
- Because of that rule, V1 should safely support customer intent capture and internal handling even if some final actions remain manual.
- Keep the solution lean and budget-conscious.

## Acceptance Criteria
1. A preorder customer can successfully log in on the website.
2. After login, they can see their own preorder record.
3. They can see their current selected product choice.
4. They can see how much they actually paid.
5. They can click Keep, Upgrade, or Cancel.
6. Each button is wired to a real working flow, not a placeholder.
7. DreamPlay can identify which customer took which action.
8. The portal language does not overpromise shipping timelines.
9. The experience works for both fully paid and 50% reservation customers.

## Verification Instructions for Tier 2
Use test accounts or real staging-safe sample orders that represent:
- one fully paid preorder
- one 50% reservation preorder

Verify that:
1. The customer can log in.
2. The portal shows the correct current selection.
3. The portal shows the correct amount paid based on `Total`.
4. Keep works and records the action.
5. Upgrade works and records or routes the request.
6. Cancel works and records or routes the request.
7. No customer can see another customer's order.
8. No language on the page commits to a delivery date unless Lionel explicitly approved it.

## Open Questions for Lionel
1. What exact website repo should Tier 2 use for this portal work?
2. Should Upgrade in V1 be:
   - request only,
   - selection flow without payment,
   - or full automated repricing/payment?
3. Should Cancel in V1 be:
   - request only,
   - or request plus immediate internal notification?
4. What is the desired customer-facing wording for preorder status?
