# DreamPlay

> Lionel's piano venture under active development.

## Concept

DreamPlay builds narrow-key digital pianos for pianists with smaller hands.
As of 2026-04-17, the product is still in the pre-production / prototype stage.

## Pricing

DreamPlay 1 pricing is $999 base and $1,899 Pro as a price anchor/decoy.

## Orders and funds

DreamPlay had about 55 preorders and roughly $18K in preorder revenue.
That preorder money is reserved for prototype and manufacturing work, not normal operating expenses.
Important customer signal: the original 3-month delivery promise was missed, but after the delay notice zero customers cancelled and several upgraded by paying $200 more.

## Order data handling

Canonical local DreamPlay order snapshots live under `data/dreamplay/orders/` in the workspace.
For order analysis, use `Total` as the source of truth for how much the customer actually paid.
Use `Lineitem name` to determine whether an order is a reservation or a full payment.
`50% Reservation` means a half reservation, and `Waitlist Reservation` should be treated separately from full orders.
DreamPlay prices increased after earlier orders, so older lineitem names and paid totals should not be treated as the current price sheet.

## Current product focus

The current product focus is a customer portal for preorder buyers.
The portal should let buyers see their status, amount paid, selected choice, and Keep / Upgrade / Cancel actions.

## Tier system

Role mapping for DreamPlay work: this main assistant is Tier 1, and any delegated implementation worker is Tier 2.
DreamPlay Tier 1 priorities are customer portal, preorder update emails, keyboard-credit integration with the masterclass funnel, conservative store maintenance, and communicating prototype progress when updates arrive.
Always escalate refunds, pricing changes, Stripe issues, customer complaints, public delivery timeline statements, and manufacturing decisions to Lionel.
DreamPlay is budget-constrained, and DreamPlay work should stay to about 20% of Lionel's total workload.
Canonical context lives in `docs/dreamplay/DREAMPLAY-TIER1-CONTEXT.md`.

## Product rules

DreamPlay One and DreamPlay Pro stay clearly distinct, gold is Pro-only, and DreamPlay Pro finishes include Aztec Gold and Nightmare Black.

### Related

- Lionel is behind DreamPlay Pianos and Musical Basics.

### Updated

2026-04-17 — Migrated from flat MEMORY.md to atomic V2 file
