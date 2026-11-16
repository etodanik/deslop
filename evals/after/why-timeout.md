It's safe only if a retry can't create a second order.

"Idempotent" means doing something twice has the same effect as doing it once, which isn't true of most POST endpoints. When your request times out, you can't tell whether the server never got it or whether it created the order and the response got lost on the way back, and if it's the second case, your retry may create a duplicate order and charge someone twice.

So find out what "idempotent" means for this endpoint. Usually it means one of two things:

- It accepts an idempotency key (often an `Idempotency-Key` header). You generate a UUID once per order, before the first attempt, and send the same one on every retry. The server sees the repeat and returns the original result.
- It dedupes on a field you send, like a client order ID. That works too, as long as the ID doesn't change between retries.

If your script generates a new key on every attempt, the server treats each retry as a new order. If the endpoint has neither mechanism, don't retry blindly. After a timeout, look the order up first (something like `GET /v2/orders?client_ref=...`) and resend only if it isn't there. Either way, use exponential backoff with jitter and cap the number of attempts.
