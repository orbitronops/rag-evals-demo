# Cloud Cost Guide

> Fictional sample document. Acme Retail is a made-up company; nothing here
> describes a real client, system, or incident.

## Right-sizing

Right-size every workload once a month. Compare the CPU and memory requests
against actual usage over the last 30 days. If a container uses less than
half of its request, lower the request. Right-sizing is the cheapest way to
reduce cloud costs, because unused requests still reserve capacity on nodes.

## Spot instances

Use spot instances for batch jobs and other workloads that can be
interrupted. Spot instances cost much less than on-demand instances, but
they can be reclaimed with two minutes of notice. Never run the checkout-api
database on spot instances. Keep stateful services on on-demand instances.

## Idle resources

Delete idle load balancers, unattached disks, and old snapshots every month.
An idle load balancer still bills every hour. Tag every resource with an
owner and a cost centre so the monthly bill can be traced to a team.
