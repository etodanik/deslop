## The token bucket in plain terms

Imagine each user has a bucket that holds tokens.

- Every request costs **one token**. If there's a token in the bucket, the request goes through and the token is removed. If the bucket is empty, the request is rejected (usually with HTTP 429).
- Tokens are added back to the bucket at a **steady rate**, say one every 0.6 seconds, which works out to 100 per minute.
- The bucket has a **maximum capacity**. Once it's full, extra tokens are discarded.

So the two settings you pick are:
- **Refill rate**: the long-run average allowed (100/min).
- **Bucket size (burst)**: how many requests a user can fire off at once after being idle.

For example, with a refill of 100/min and capacity of 100, a user who's been quiet can send 100 requests instantly, then has to wait for tokens to trickle back at about 1.67 per second. If you set capacity to 20, they can only burst 20 at once but still average 100/min over time.

## Does it fit?

Yes, it's a good fit for "100 requests per minute per user," and it's one of the most common choices. Reasons:

- **Allows bursts** but enforces the average, which matches how real clients behave (a page load fires several calls at once).
- **Cheap to implement**: per user you only store two numbers: the current token count and the last refill timestamp. You compute the refill lazily when a request arrives, so there's no background timer.
- **Easy to explain** to API consumers, and you can return headers like `Retry-After` or `X-RateLimit-Remaining`.

## Alternatives, briefly

- **Fixed window** (count per calendar minute): simplest, but a user can send 100 at 12:00:59 and 100 more at 12:01:00, giving 200 in two seconds.
- **Sliding window log/counter**: more precise, no boundary problem, but uses more memory (log) or is slightly approximate (counter).
- **Leaky bucket**: smooths traffic to a constant output rate. Good if the backend can't tolerate bursts at all.

## Things to decide

1. **Burst size.** Do you want to allow a full 100 at once, or something smaller? Match it to what your backend can handle.
2. **Where state lives.** With multiple API servers, per-user counts must be shared. Redis is the usual answer, using a Lua script (or an atomic operation) so the read-modify-write on the bucket isn't racy.
3. **Identifying "user."** API key, auth token user ID, or IP for unauthenticated traffic.
4. **Response behavior.** Return 429 with `Retry-After` so well-behaved clients can back off.

Many API gateways (Kong, NGINX, Envoy, AWS API Gateway) offer token-bucket-style limiting out of the box, so check before building it yourself.
