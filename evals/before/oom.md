## What's going on

`OOMKilled` means the container used more memory than its limit, so the Linux kernel's out-of-memory killer terminated it (exit code 137). Kubernetes then restarts the container per the pod's restart policy, and if it keeps happening you get `CrashLoopBackOff`.

Important detail: the limit is enforced per container through cgroups. It doesn't matter how much free memory the node has. If the container crosses its own `resources.limits.memory`, it gets killed.

## Confirm it

```bash
kubectl describe pod <pod-name>
```

Look under `Last State` for `Reason: OOMKilled` and `Exit Code: 137`. To see actual usage:

```bash
kubectl top pod <pod-name> --containers
```

If you have Prometheus/Grafana, graph `container_memory_working_set_bytes` against the limit and you'll typically see a line climbing until it hits the ceiling.

## Why it happens

1. **The limit is too low** for the app's normal working set.
2. **A memory leak**: usage grows steadily over time until it's killed.
3. **Spiky workloads**: a big request, batch job, or large payload briefly needs much more memory.
4. **Runtime not aware of the container limit**: e.g. a JVM with a heap (`-Xmx`) set near or above the container limit, or Node.js/Go/Python defaults sizing themselves from the host's memory. Heap isn't the only memory use either: threads, metaspace, buffers, and native allocations all count.
5. **Memory-backed volumes** (`emptyDir` with `medium: Memory`) and tmpfs count against the limit too.

## What to change

**Short-term, raise the limit** (and request) in the pod spec:

```yaml
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "1Gi"
```

Set the request close to what the app normally uses and the limit with some headroom above peak. Don't set it so high that it risks starving the node.

**Then fix the cause:**
- **JVM**: use `-XX:MaxRAMPercentage=75` (or set `-Xmx` to about 70-75% of the limit) to leave room for non-heap memory.
- **Node**: set `--max-old-space-size` below the container limit.
- **Leaks**: take a heap profile and look for unbounded caches, growing collections, unclosed connections, or per-request objects being retained.
- **Spikes**: stream large payloads instead of loading them in memory, cap batch sizes, or add pagination.
- **Scale out** with more replicas if each pod is simply handling too much load.

Start by confirming the usage pattern: if memory climbs steadily, suspect a leak; if it's flat and then hits the limit, the limit is probably just too low.
