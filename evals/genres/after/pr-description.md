## Summary

This replaces the hand-rolled retry loop in the billing worker with exponential backoff and jitter, and caps retries at 5 attempts.

## Problem

The old loop had a bug: failed charges were retried every second, forever. That put needless load on the payment provider and on our own infrastructure, risked the provider rate limiting us, and meant a failed charge never resolved.

## Changes

- Replaced the custom retry loop with exponential backoff.
- Added jitter so retries spread out and avoid thundering herd problems.
- Capped retries at 5 attempts, after which the charge is marked as failed.
- Added unit tests for backoff timing, jitter bounds and the maximum number of attempts.

## Testing

The new unit tests check that failed charges stop retrying after 5 attempts and that delays grow exponentially between attempts. All existing tests pass.

## Notes for reviewers

Look closely at the backoff parameters (base delay and max delay). They may need tuning to the payment provider's rate limits, and I'm happy to adjust them based on your feedback.
