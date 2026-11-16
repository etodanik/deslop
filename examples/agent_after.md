I found the bug. When a request times out, the retry wrapper catches the exception and returns `None`, so the caller can't tell that the request failed. The queue worker then treats the job as successful and acknowledges it. The failure path and the success path return the same value, which is why this never showed up in the logs.

I changed `worker/retry.py` so that when the wrapper runs out of retries, it raises a new `RetryExhausted` error that carries the original exception. Callers can catch it. The new behavior is off by default behind the `STRICT_RETRY` flag, so we can turn it on for a few job types first.

I also split the retry metrics by job type, so the dashboard shows which jobs retry the most.

Changes:
- When retries run out, the wrapper raises `RetryExhausted` instead of returning `None`.
- The worker only acknowledges a job if the wrapper returned a result.
- A new test covers the case that used to pass silently.

Two things are unfinished. Two integration tests are skipped because they need a Redis fixture that I couldn't find. And `STRICT_RETRY` isn't in the config schema yet, so for now the code falls back to a default value. Note that session-token refresh goes through the same wrapper, so it gets this change too.
