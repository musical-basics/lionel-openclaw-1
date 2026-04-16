# DreamPlay Customer Portal V1 Spec

## Goal

Preorder buyers should be able to log in, view their preorder status, see their current selected choice, and submit one of three actions:

- Keep
- Upgrade
- Cancel

This must be accurate, simple, and safe for high-trust preorder customers.

## Recommended V1 Architecture

Build a small customer portal inside the DreamPlay website repo.

Key principles:
- Shopify remains the system of record for orders
- server-side Shopify Admin API only, never client-side token exposure
- no custom database required for v1 unless repo realities force it
- store portal-specific state on the Shopify order via metafields and/or tags

## Recommended Auth For V1

Use a simple server-side magic-link flow tied to preorder identity.

Preferred v1 path:
- customer enters email + order number on `/preorder/login`
- server verifies matching Shopify order/customer
- server sends a one-time signed login link
- customer lands in portal session for that order

Why this is the safest v1:
- avoids blocking on full customer-account migration
- avoids exposing other order data
- keeps auth narrow to preorder access

If the repo already has a good existing customer auth system, reuse it only if that is clearly faster and safer.

## Customer Portal V1 Data To Show

For each preorder buyer, display:

- order number
- order date
- payment status
- fulfillment status
- current preorder item / variant
- quantity
- amount paid
- current selected choice / portal status
- estimated ship window, if available
- any action availability or policy message

## Portal Choice State

Recommended Shopify order metafields/tags for v1:

- `preorder.choice`
  - `none`
  - `keep`
  - `cancel_requested`
  - `cancelled`
  - `upgrade_requested`
  - `upgraded`
- `preorder.choice_updated_at`
- `preorder.upgrade_target_variant_id`
- `preorder.last_portal_action_id`

These let the portal stay lightweight while keeping order truth attached to Shopify.

## Recommended Route Shape

- `GET /preorder/login`
- `POST /preorder/request-link`
- `GET /preorder/auth?token=...`
- `GET /preorder/orders/[orderId]`
- `POST /preorder/orders/[orderId]/keep`
- `POST /preorder/orders/[orderId]/cancel`
- `POST /preorder/orders/[orderId]/upgrade`

## Button Wiring For V1

### Keep
Safest to automate immediately.

Behavior:
- write `preorder.choice=keep`
- write timestamp
- add idempotency key / action key
- optionally add order tag for internal visibility

### Cancel
Do not blindly auto-cancel every order.

V1 behavior:
- if order is a pure preorder, unfulfilled, and within approved policy, allow backend cancellation flow via Shopify `orderCancel`
- otherwise record `cancel_requested` and route to manual review
- must be idempotent and protected against duplicate refunds

### Upgrade
Do not ship this as a fake button.

V1 safest behavior:
- record requested upgrade target server-side
- if Lionel provides a clean one-to-one upgrade mapping and test-store validation passes, automate via Shopify order edit + invoice/send-payment flow
- otherwise make it a real backend request flow that records `upgrade_requested` for manual handling, not a dead-end placeholder

## Acceptance Criteria

A valid preorder customer should be able to:

1. log in without account enumeration issues
2. see the correct Shopify-backed order
3. see their current portal choice/status
4. press Keep and have the result recorded idempotently
5. press Cancel and either:
   - complete a valid backend cancellation, or
   - safely enter manual review state
6. press Upgrade and either:
   - enter a validated automated upgrade flow, or
   - safely enter manual review state

System-level acceptance criteria:
- Shopify tokens stay server-side only
- no duplicate cancel or upgrade mutations
- fulfilled/ineligible orders cannot be wrongly cancelled
- action state is visible in Shopify-backed metadata
- all flows verified against dev/test data before release

## Safest First Build Slice

Build in this order:

### Slice 1
- preorder login
- portal session
- read-only order/status view
- visible current choice/status

### Slice 2
- Keep action wired fully

### Slice 3
- guarded Cancel backend flow

### Slice 4
- guarded Upgrade backend flow

This keeps the first release narrow and reduces refund/change risk.

## Inputs Needed Before Implementation

From Lionel:

- website repo access for the DreamPlay site
- Shopify shop domain
- Shopify custom app Admin API token
- required Shopify scopes
- preorder product / variant IDs
- upgrade mapping, if upgrades should be automated
- cancel / refund cutoff rules
- support email / copy for portal messaging
- whether current site auth/accounts already exist and are worth reusing

## Important Constraints

- keep v1 narrow
- avoid expensive architecture
- do not overpromise delivery timing in UI copy
- preserve Shopify as source of truth where possible
- do not redesign the whole DreamPlay site to get this shipped

## Immediate Next Step

Once repo access is provided, implementation should begin with:
- repo inspection
- auth surface inspection
- Shopify integration surface inspection
- building Slice 1 first
