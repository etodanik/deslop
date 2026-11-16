## What consumer lag means

Consumer lag is the number of messages that have been written to a Kafka topic but not yet processed by a consumer group. In other words, it's the gap between the latest offset (where producers are writing) and the committed offset (where your consumers have read up to).

A lag of 2 million means your consumers are 2 million messages behind.

## Is it bad?

It depends on two things: **whether it's growing** and **how fast you process**.

- **Stable lag**, even a large one, can be fine if consumers are keeping pace and the data isn't time-sensitive.
- **Steadily climbing lag**, which is what you're seeing, is a problem. It means producers are writing faster than consumers can process, and the backlog will keep growing until something changes (or you hit retention limits).

A useful way to translate it: divide the lag by your consumer's processing rate. If you process 5,000 msgs/sec, 2 million messages is about 400 seconds (~7 minutes) of delay. If you process 100/sec, it's over 5 hours.

## What it means for users

Whatever the consumer does is happening late. Depending on your system, that could be:

- Order confirmations, emails or notifications arriving minutes or hours late
- Dashboards, search indexes, or recommendations showing stale data
- Payments or inventory updates lagging behind reality
- Downstream services seeing old state

If the consumer feeds something user-facing and real-time, users are probably already noticing. If it's analytics or batch work, it may be invisible.

There's also a risk of **data loss**: if lag grows beyond the topic's retention period (default 7 days), messages get deleted before they're ever consumed.

## What to check

1. **Did something change?** A deploy, a traffic spike, a slower downstream dependency (database, external API)?
2. **Are consumers healthy?** Look for crashes, rebalances, long GC pauses, or a consumer repeatedly failing on a "poison" message and retrying.
3. **Is the lag evenly spread across partitions?** If one partition has most of it, you may have a hot key or one stuck consumer.
4. **Is processing slow?** Profile what each message does. Slow DB writes or synchronous HTTP calls are common culprits.

## Fixes

- **Add consumers**, up to the number of partitions (consumers beyond that sit idle). If you need more parallelism, increase the partition count.
- **Speed up processing**: batch writes, parallelize within a consumer, remove blocking calls.
- **Tune consumer settings**: `max.poll.records`, `fetch.min.bytes`, and make sure `max.poll.interval.ms` isn't causing rebalances.
- **Handle poison messages** with a dead-letter queue so one bad record doesn't block a partition.

Set an alert on lag *growth rate* or time-lag rather than only on absolute lag, so you catch this earlier next time.
