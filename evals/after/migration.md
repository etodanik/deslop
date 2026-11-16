Your migration is probably holding a lock, or waiting for one. Check `pg_stat_activity` and `pg_locks` to see what's blocking, cancel the migration with `pg_cancel_backend(pid)`, and make sure the table is back to normal before you try again.

It hangs because a `NOT NULL` column needs a value in every existing row, and there are three ways that goes wrong on a 20 GB table. Before Postgres 11, adding a column with a `DEFAULT` rewrites the whole table under an `ACCESS EXCLUSIVE` lock, and every read and write queues behind it. From 11 on, a constant default is instant (metadata only), but a volatile one like `now()` or `random()` still forces a rewrite. With no default at all, `ADD COLUMN ... NOT NULL` simply fails, because the existing rows would break the constraint. And even a fast `ALTER` needs a brief exclusive lock, so if a long-running transaction is already using the table, the `ALTER` waits for it and every new query waits for the `ALTER`.

A backfill means filling in the new column for existing rows as its own step, in small batches, separate from the schema change. Updating, say, 10,000 rows at a time keeps each lock short, keeps WAL and replication lag under control, and lets the app keep running.

The usual sequence:

1. Add the column as nullable, with no default (or a constant default on PG 11+). Set a lock timeout first so it fails fast instead of blocking everything:
   ```sql
   SET lock_timeout = '3s';
   ALTER TABLE orders ADD COLUMN status text;
   ```
2. Change the app to write the column on every insert and update, so new nulls stop appearing.
3. Backfill in batches:
   ```sql
   UPDATE orders SET status = 'pending'
   WHERE id IN (
     SELECT id FROM orders WHERE status IS NULL LIMIT 10000
   );
   ```
   Run this in a loop from a script until it updates zero rows. Commit each batch, sleep briefly between batches, watch replication lag, and consider running it off-peak.
4. Enforce the constraint without a long lock. A plain `SET NOT NULL` scans the table under a strong lock, so add a check constraint first:
   ```sql
   ALTER TABLE orders ADD CONSTRAINT status_not_null
     CHECK (status IS NOT NULL) NOT VALID;
   ALTER TABLE orders VALIDATE CONSTRAINT status_not_null;
   ```
   `VALIDATE` still scans the table, but it takes a light lock, so writes keep going. On PG 12+, `ALTER TABLE orders ALTER COLUMN status SET NOT NULL;` is then instant, because Postgres can rely on the validated constraint. After that you can drop the check constraint.
