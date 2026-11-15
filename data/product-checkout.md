# Checkout Service Overview

> Fictional sample document. Acme Retail is a made-up company; nothing here
> describes a real client, system, or incident.

## What checkout-api does

checkout-api takes a customer's basket, charges their payment method, and
creates an order. It runs as a Kubernetes deployment in the prod namespace
with three replicas. It depends on the payments service and the orders
database. If payments is down, checkout-api returns an error instead of
taking a payment it cannot complete.

## Resource limits

The memory limit for checkout-api is 512Mi per container, and the CPU limit
is 1 CPU per container. The memory request is 256Mi. If the container is
killed with exit code 137, it was OOMKilled, which means the memory limit was
too low for the traffic it was serving. Raise the limit only after checking
the memory usage graph.

## Database

checkout-api uses a PostgreSQL database called orders-db. The database runs
on a managed PostgreSQL service with daily backups. The connection string is
stored in a Kubernetes secret named checkout-db-credentials. Never commit a
database password to git.
