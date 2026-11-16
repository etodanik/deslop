A steadily climbing lag is bad. It means producers are writing faster than your consumers can keep up, and the backlog will keep growing until something changes. A large lag that holds steady can be fine, as long as your consumers keep pace with new messages.

Lag is the number of messages written to the topic that your consumer group hasn't processed yet, so you're 2 million messages behind. To turn that into time, divide by your processing rate. At 5,000 messages a second it's about 7 minutes of delay. At 100 a second it's over 5 hours.

For users, whatever this consumer does is now happening late: order confirmations, emails and notifications, search indexes and dashboards, payments or inventory updates, and any service downstream of them. If it feeds something user-facing and real-time, people have probably noticed already. If it's analytics, they may not see it at all. There's also a data-loss risk. If the lag outgrows the topic's retention period (7 days by default), Kafka deletes messages before anyone reads them.

To find the cause:

1. Check whether anything changed: a deploy, a traffic spike, or a slower database or external API.
2. Check the consumers' health. Look for crashes, rebalances, long GC pauses, or one consumer retrying the same poison message over and over.
3. Look at lag per partition. If one partition holds most of it, you probably have a hot key or a stuck consumer.
4. Look at what each message does. Slow database writes and synchronous HTTP calls are the usual suspects.

To fix it, you can add consumers, but only up to the partition count. Past that they sit idle, so add partitions if you need more parallelism. You can also speed up processing by batching writes, parallelizing inside the consumer, and removing blocking calls. Tune `max.poll.records` and `fetch.min.bytes`, and make sure `max.poll.interval.ms` isn't triggering rebalances. Send poison messages to a dead-letter queue so one bad record can't block a partition. And next time, alert on how fast the lag is growing, or on time-lag, not just the absolute number.
