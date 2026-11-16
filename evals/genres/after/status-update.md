Hi team,

Here's where we stand on the data pipeline migration this week.

The migration is about 70% done. Two tables are blocked until the analytics team makes a schema decision, and I'm following up with them so we can keep moving.

We also found that the nightly job was silently skipping rows with null timestamps. That's fixed now, and we'll watch the next few runs to confirm everything is processing as expected.

Next, we need a decision from analytics on the blocked tables, we'll keep migrating the remaining tables, and we'll monitor the nightly job to verify the fix.

Thanks for all the work, everyone.
