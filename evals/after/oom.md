The container used more memory than its limit, so the kernel's out-of-memory killer stopped it (exit code 137). Kubernetes restarts it under the pod's restart policy, and if this keeps happening you'll see `CrashLoopBackOff`. The limit applies to each container separately, through cgroups. Free memory on the node doesn't help. Once a container goes over its own `resources.limits.memory`, it gets killed.

To confirm, run `kubectl describe pod <pod-name>` and look under `Last State` for `Reason: OOMKilled` and `Exit Code: 137`. `kubectl top pod <pod-name> --containers` shows current usage. If you have Prometheus, graph `container_memory_working_set_bytes` against the limit. You'll usually see it climb until it hits the ceiling.

The shape of that graph tells you the cause. If memory climbs steadily, suspect a leak. If it's flat and then hits the limit, the limit is probably just too low for the app. Sudden spikes point to big requests, batch jobs or large payloads. A common trap is a runtime that doesn't know about the container limit: a JVM with `-Xmx` set close to or above it, or Node, Go or Python sizing themselves from the host's memory. The heap isn't the only thing that counts, either. Threads, metaspace, buffers, native allocations and memory-backed `emptyDir` volumes all count toward the limit.

For now, raise the request and the limit:

```yaml
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "1Gi"
```

Set the request near what the app normally uses and the limit a bit above its peak, but not so high that one pod can starve the node.

Then fix the cause. On the JVM, use `-XX:MaxRAMPercentage=75`, or set `-Xmx` to about 70–75% of the limit, so there's room for non-heap memory. On Node, set `--max-old-space-size` below the limit. For a leak, take a heap profile and look for unbounded caches, collections that keep growing, unclosed connections, or per-request objects that stick around. For spikes, stream large payloads instead of loading them into memory, and cap batch sizes or paginate. If each pod is simply carrying too much load, add replicas.
