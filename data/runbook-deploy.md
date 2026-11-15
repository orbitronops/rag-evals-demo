# Deployment Runbook — checkout-api

> Fictional sample document. Acme Retail is a made-up company; nothing here
> describes a real client, system, or incident.

## Deploying checkout-api

To deploy checkout-api, run `kubectl apply -f k8s/checkout-api.yaml -n prod`
from the release branch, then watch the rollout with
`kubectl rollout status deployment/checkout-api -n prod`. A deployment is
only complete when the rollout reports success and the readiness probe is
passing. Never deploy directly from a laptop branch; only the release branch
may be applied to prod.

## Rollback

To roll back a failed deployment, run
`kubectl rollout undo deployment/checkout-api -n prod`. Then check the
previous revision with `kubectl rollout history deployment/checkout-api -n prod`
and confirm the old pods are Ready before telling the on-call engineer the
rollback is done. A rollback needs no change approval, because it restores
the last known good version.

## Approval

Every production deployment needs approval from the on-call engineer and a
second reviewer in the #deploys channel. Approval is recorded in the deploy
ticket. Emergency fixes still need one approver, but the second review may
happen after the deploy.
