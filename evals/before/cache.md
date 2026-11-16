## Why prices are stale

You're almost certainly seeing a classic caching issue: the cache holds the old value, and nothing tells it that the price changed. Redis keeps serving the cached entry until it either expires or is removed. A 10-minute staleness window strongly suggests a **TTL of 600 seconds** on the price keys, with no invalidation on update.

The typical flow looks like this:

1. A read comes in, Redis misses, you load from the DB, and store the price in Redis with a 10-minute TTL.
2. Someone updates the price in the database.
3. Redis still has the old value, so readers get stale data until the TTL runs out.

Other possible contributors worth ruling out:
- **Multiple cache layers**: a CDN, HTTP caching headers (`Cache-Control: max-age=600`), or an in-process cache in the app, in addition to Redis.
- **Read replicas**: if you read from a replica after an update, replication lag can briefly cause a stale re-cache.
- **A race**: a reader fetches the old value from the DB just before the update, then writes it into the cache just after you invalidate, which re-poisons the cache.

## The fix

**Invalidate (or update) the cache when the price changes.** The most common pattern is cache-aside with invalidation on write:

```python
def update_price(product_id, new_price):
    db.update_price(product_id, new_price)
    redis.delete(f"price:{product_id}")   # next read repopulates from DB
```

Alternatives:
- **Write-through**: write the new price to the DB and set it in Redis at the same time. Readers always see fresh data, at the cost of a bit more write logic.
- **Event-driven invalidation**: if prices are updated by another service or a batch job, publish a "price changed" event and have a consumer delete or refresh the keys. Or use change data capture (e.g. Debezium) from the DB.

Make sure **every** code path that modifies prices (admin tools, imports, scripts) goes through the invalidation, since one missed path gives you the bug again.

## Safety nets

- **Keep a TTL as a backstop**, but shorter (e.g. 30-60 seconds), so that if an invalidation is missed the staleness is bounded.
- **Order the operations carefully**: update the DB first, then delete the cache key. Doing it the other way round widens the race window.
- To handle the race I mentioned, you can use short TTLs, versioned keys (`price:{id}:v{version}`), or delete the key again shortly after the write ("delayed double delete").

If you tell me how prices get updated (admin UI, import job, another service), I can suggest where the invalidation should hook in.
