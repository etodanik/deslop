## Why the migration hangs

Adding a `NOT NULL` column to an existing table means every existing row needs a value for it. Depending on how the migration is written and your Postgres version, a few things can go wrong on a 20 GB table:

- If there's a `DEFAULT`, older Postgres versions (before 11) rewrite the entire table while holding an `ACCESS EXCLUSIVE` lock. Everything else (reads and writes) queues up behind it, so it looks like a hang. In Postgres 11+, adding a column with a *constant* default is fast (metadata only), but a volatile default (like `now()` or `random()`) still triggers a full rewrite.
- If there's **no default**, `ADD COLUMN ... NOT NULL` fails outright because existing rows would violate the constraint.
- Even if the `ALTER` itself is quick, it needs a brief exclusive lock. If a long-running transaction holds a lock on the table, your `ALTER` waits for it, and every query behind it waits for the `ALTER`. That pile-up looks like a hang as well.

## What a backfill is

A backfill is populating the new column's values for existing rows, usually in small batches, as a separate step from changing the schema. Rather than one giant statement touching 20 GB at once under a lock, you update rows in chunks (e.g. 10,000 at a time) so locks stay short, WAL and replication lag stay manageable, and the app keeps working.

## The safe approach (expand, backfill, contract)

1. **Add the column as nullable**, with no default (or a constant default on PG 11+). This is nearly instant:
   ```sql
   ALTER TABLE orders ADD COLUMN status text;
   ```
   Also set `lock_timeout` so it fails fast instead of blocking everything:
   ```sql
   SET lock_timeout = '3s';
   ```

2. **Update your application** to write the new column for all new/updated rows (so you aren't racing against new nulls).

3. **Backfill existing rows in batches**, e.g.:
   ```sql
   UPDATE orders SET status = 'pending'
   WHERE id IN (
     SELECT id FROM orders WHERE status IS NULL LIMIT 10000
   );
   ```
   Loop this from a script until zero rows are updated, with a short sleep between batches. Commit each batch separately. Watch replication lag and consider running it off-peak.

4. **Enforce NOT NULL without a long lock.** A plain `SET NOT NULL` scans the whole table under a strong lock. Instead:
   ```sql
   ALTER TABLE orders ADD CONSTRAINT status_not_null
     CHECK (status IS NOT NULL) NOT VALID;
   ALTER TABLE orders VALIDATE CONSTRAINT status_not_null;
   ```
   `VALIDATE` scans the table but only takes a light lock, so writes continue. Then (on PG 12+) `ALTER TABLE orders ALTER COLUMN status SET NOT NULL;` is instant, since Postgres can use the validated check constraint to skip the scan. You can then drop the redundant check constraint.

## Right now

Your hung migration is probably holding or waiting for a lock. Check `pg_stat_activity` and `pg_locks` for what's blocking, cancel the migration (`pg_cancel_backend(pid)`), and confirm the table is back to normal before retrying with the approach above.
