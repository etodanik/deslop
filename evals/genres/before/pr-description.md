## Summary

This PR replaces the hand-rolled retry loop in the billing worker with a proper exponential backoff strategy with jitter, and caps retries at a maximum of 5 attempts.

## Problem

The previous retry logic had a bug where failed charges were retried every second indefinitely. This could result in:

- Unnecessary load on the payment provider and our own infrastructure
- Potential rate limiting or throttling from the provider
- Failed charges retrying forever with no resolution

## Changes

- Replaced the custom retry loop with exponential backoff
- Added jitter to spread out retries and avoid thundering herd problems
- Introduced a maximum of 5 retry attempts, after which the charge is marked as failed
- Added unit tests covering the new retry behavior, including backoff timing, jitter bounds, and max attempts

## Testing

- Added new unit tests for the retry logic
- Verified that failed charges stop retrying after 5 attempts
- Verified that delays increase exponentially between attempts
- All existing tests pass

## Notes for Reviewers

Please pay particular attention to the backoff parameters (base delay and max delay), as these may need tuning based on the payment provider's rate limits. Happy to adjust based on feedback.
