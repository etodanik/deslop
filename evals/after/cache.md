Nothing tells Redis the price changed. It keeps serving the cached entry until it expires, and a 10-minute window suggests your price keys have a 600-second TTL with no invalidation on update: a read misses, you load the price from the database and cache it, someone changes the price, and every reader gets the old one until the TTL runs out.

The fix is to delete or update the cache entry whenever the price changes:

```python
def update_price(product_id, new_price):
    db.update_price(product_id, new_price)
    redis.delete(f"price:{product_id}")   # next read repopulates from DB
```

You could also write the new price to the database and to Redis at the same time (write-through). If prices change in another service or a batch job, have it publish a "price changed" event and let a consumer clear the keys, or use change data capture such as Debezium. Whichever you choose, every path that changes prices has to go through it, including admin tools, imports and one-off scripts. Miss one and the bug comes back.

Keep a TTL as a backstop, but shorten it to something like 30–60 seconds, so a missed invalidation doesn't last long. Update the database first and delete the key second. Doing it the other way round widens a race in which a reader fetches the old price just before your update and writes it back into the cache just after you cleared it. Short TTLs, versioned keys (`price:{id}:v{version}`), or deleting the key a second time shortly after the write all prevent that race.

If the fix doesn't fully work, check for other caches too: a CDN, `Cache-Control: max-age=600` headers, or an in-process cache in the app. And if you read from a replica right after an update, replication lag can put the old price back into Redis.
