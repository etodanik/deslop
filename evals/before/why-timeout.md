Short answer: it's safe **if** the endpoint is truly idempotent, but a timeout is exactly the case where you need to be careful about what "idempotent" means in practice.

## What idempotent means

An operation is idempotent if doing it once has the same effect as doing it many times. `PUT /orders/123` with the same body is a classic example: no matter how many times you send it, you end up with one order in the same state. `POST` is normally *not* idempotent, because each call typically creates a new resource. Send it twice and you get two orders.

## Why timeouts are the tricky case

When a request times out, you don't know what happened. Either:

1. The server never got the request, or
2. The server got it, processed it (created the order), and the response was lost or too slow.

If you retry in case 2 and the endpoint isn't really idempotent, you've created a duplicate order, and possibly charged someone twice.

## What to check

- **Does the API actually guarantee idempotency for POST /v2/orders?** Many APIs do this with an **idempotency key**: you generate a unique ID (e.g. a UUID) per logical order and send it in a header like `Idempotency-Key`. The server remembers the key and returns the original result on a repeat instead of creating a new order. Check the docs to see if that's what "idempotent" means here.
- **Is your script reusing the same key across retries?** If it generates a new key on each attempt, you get no protection at all.
- **Does the retry have backoff and a cap?** Use exponential backoff with jitter and a max attempt count, so you don't hammer a struggling service.

## Practical recommendation

- If there's an idempotency key mechanism: generate the key once before the first attempt, reuse it on every retry. Safe.
- If the endpoint is "idempotent" only because it dedupes on some natural field (like a client-supplied order ID in the body), that's also fine, as long as that ID is stable across retries.
- If neither is the case, don't blindly retry. After a timeout, query the order (e.g. `GET /v2/orders?client_ref=...`) to see whether it was created before deciding to resend.

So: ask whoever owns the endpoint exactly what the idempotency guarantee is, and make sure your script sends the same key or ID on every retry.
