# DreamPlay orders

Canonical local order snapshots for assistant use.

## Business rules
- Use `Total` as the source of truth for how much the customer actually paid.
- Use `Lineitem name` to determine whether the order is a reservation or a full payment.
- Current DreamPlay prices have increased, so older orders should not be used as the current price sheet.

## Files
- `imports/2026-04-16-shopify-export.csv` - raw Shopify export provided by Lionel. Kept local and intentionally not tracked in git.
- `2026-04-16-orders-normalized.csv` - assistant-friendly normalized snapshot. Kept local and intentionally not tracked in git.
- `2026-04-16-orders-summary.json` - summary stats and parsing rules for this snapshot.
