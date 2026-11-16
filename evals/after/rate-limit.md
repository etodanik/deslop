Yes, a token bucket fits. It's one of the most common ways to do "100 requests per minute per user."

Picture one bucket of tokens per user. Each request takes a token. If the bucket is empty, you reject the request, usually with a 429. Tokens drip back in at a steady rate, here one every 0.6 seconds, which comes to 100 a minute. The bucket has a maximum size, and tokens that arrive when it's full are thrown away.

That leaves you two numbers to pick. The refill rate is the long-run average you allow (100/min). The bucket size is how many requests a user can send at once after a quiet period. With a size of 100, an idle user can fire 100 requests immediately and then gets about 1.67 a second. With a size of 20, they can burst only 20, but they still average 100 a minute.

It suits your case for three reasons. Real clients are bursty (one page load fires several calls at once), and a token bucket allows that while holding the average. It's cheap: for each user you store the token count and the time of the last refill, and you work out the refill when a request arrives, so there's no background timer. It's also easy to explain to API users, and it maps directly onto `Retry-After` and `X-RateLimit-Remaining` headers.

The alternatives each have a catch. A fixed window (count per calendar minute) is the simplest, but a user can send 100 requests at 12:00:59 and another 100 at 12:01:00. A sliding window avoids that, but it either uses more memory (log) or is slightly approximate (counter). A leaky bucket smooths everything to a constant rate, which you want only if the backend can't take bursts at all.

What you'll still need to decide:

1. Bucket size. Pick it to match what your backend can absorb.
2. Where the state lives. With more than one API server, the counts have to be shared. Redis is the usual choice, with a Lua script or another atomic operation so concurrent requests can't race on the read-modify-write.
3. Who counts as a user: the API key, the user ID from the auth token, or the IP for unauthenticated traffic.
4. What to return. Send 429 with `Retry-After` so well-behaved clients back off.

Check your API gateway before you build this yourself. Kong, NGINX, Envoy and AWS API Gateway all offer something like it.
