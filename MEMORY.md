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

## DreamPlay order handling
- Canonical local DreamPlay order snapshots live under `data/dreamplay/orders/` in the workspace.
- For DreamPlay order analysis, use `Total` as the source of truth for how much the customer actually paid.
- Use `Lineitem name` to determine whether an order is a reservation or a full payment. `50% Reservation` means a half reservation, and `Waitlist Reservation` should be treated separately from full orders.
- DreamPlay prices increased after earlier orders, so older lineitem names and paid totals should not be treated as the current price sheet.
