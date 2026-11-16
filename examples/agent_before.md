Root cause found. The retry wrapper swallows the timeout and the caller never knows the request failed — so the queue worker thinks the job succeeded and acks it. This is where the asymmetry bites: the happy path and the failure path converge on the same return value.

Fix landed in `worker/retry.py`. Now gated behind `STRICT_RETRY` so we can derisk the rollout. Surfaced the underlying exception via a new `RetryExhausted` error the caller can catch. Also bucketed the retry metrics by job type so the dashboard tells us which jobs are burning their retry budget.

Changes:
- retry budget exhaustion handling → raises instead of returning None
- job ack logic checks result the wrapper now returns
- added test the old behavior would have passed silently

The test suite wants a Redis fixture I couldn't find, so two integration tests are skipped. The config doesn't know about the new flag yet either — I papered over that with a default. Worth noting the session token refresh path hits the same wrapper, so it inherits the fix.
