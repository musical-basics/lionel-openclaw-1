# MEMORY

## Communication preferences
- Lionel prefers brief, direct, action-oriented responses.
- After each response, proactively surface the next concrete step, especially for setup or getting things working properly.

## Ongoing projects
- Teachable migration is happening. Keep that as active context, but do not retain extra migration detail unless Lionel asks for it.

## Work profile
- Lionel is a YouTuber and needs to produce a high volume of content.

## Life direction
- Lionel does not see Las Vegas as a long-term place to stay.
- If he leaves, Germany is a place he genuinely wants to try living.
- He feels a strong connection to the German language and to Beethoven as a classical pianist.

## DreamPlay Tier 1 context
- Canonical DreamPlay business-agent context lives in `DREAMPLAY-TIER1-CONTEXT.md`.
- DreamPlay builds narrow-key digital pianos for pianists with smaller hands.
- DreamPlay 1 pricing context: $999 base and $1,899 Pro as a price anchor/decoy. Current status is pre-production, with prototype work in progress through a manufacturing partner.
- DreamPlay had 55 preorders and about $18K in preorder revenue, and that money is reserved for prototype/manufacturing work, not normal operations.
- Important customer signal: the original 3-month delivery promise was missed, but after the delay notice zero customers cancelled and several upgraded by paying $200 more.
- Tier 1 priorities are customer portal, preorder update emails, keyboard-credit integration with the masterclass funnel, conservative store maintenance, and communicating prototype progress when updates arrive.
- Always escalate DreamPlay refunds, pricing changes, Stripe issues, customer complaints, public delivery timeline statements, and manufacturing decisions to Lionel.
- DreamPlay is budget-constrained, and DreamPlay work should stay to about 20% of Lionel's total workload.

## DreamPlay order handling
- Canonical local DreamPlay order snapshots live under `data/dreamplay/orders/` in the workspace.
- For DreamPlay order analysis, use `Total` as the source of truth for how much the customer actually paid.
- Use `Lineitem name` to determine whether an order is a reservation or a full payment. `50% Reservation` means a half reservation, and `Waitlist Reservation` should be treated separately from full orders.
- DreamPlay prices increased after earlier orders, so older lineitem names and paid totals should not be treated as the current price sheet.
