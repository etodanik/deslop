Don't shard yet. A single Postgres instance handles 40 million rows fine, and sharding adds a lot of operational and application complexity. There are almost certainly cheaper fixes.

First find out why the reads are slow. Pull the slowest and most frequent queries from `pg_stat_statements` (or the slow query log) and run:

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

Look for sequential scans where you expected an index, big gaps between estimated and actual row counts (stale statistics), and lots of buffer reads from disk instead of cache.

Most of the time the fix is one of these:

- Indexes that match your real `WHERE`, `JOIN` and `ORDER BY` clauses. Column order matters in composite indexes. Partial indexes and covering indexes (`INCLUDE`) can take a query from seconds to milliseconds.
- Fresh statistics. Run `ANALYZE` and check that autovacuum is keeping up, because dead-tuple bloat slows reads too.
- Better queries. Watch for `SELECT *`, `OFFSET` pagination deep into the table (switch to keyset pagination), functions wrapped around indexed columns, and N+1 queries from the app.
- Memory settings. `shared_buffers`, `work_mem` and `effective_cache_size` are often still at their defaults.

If that isn't enough, you can still scale reads without sharding. Add read replicas, cache hot reads in Redis or the app, or partition the table by date or tenant. Partitioning keeps it one database, but queries can skip partitions they don't need. More RAM, so the working set fits in memory, is often the cheapest option of all.

Sharding starts to make sense when one node can't keep up with writes, when storage reaches multiple terabytes, or when replicas and caching can't absorb the load. Even then, look at Citus before you build your own.
