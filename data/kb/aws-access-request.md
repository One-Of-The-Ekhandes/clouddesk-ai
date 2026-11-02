---
title: Requesting access to AWS resources (S3, DynamoDB, Lambda, Athena)
category: cloud_access
team: cloud_team
---
Access is granted through IAM groups, never by attaching policies to individual users.

Standard groups:
- dev-readonly: read-only access to development and staging.
- dev-deployers: deploy Lambda and ECS services in development.
- data-analysts: Athena queries and read access to the analytics S3 buckets.
- prod-operators: production changes; needs manager approval and cloud team sign-off.

Read access to non-production can be handled by the service desk by adding the user to the right group.
Any production write access, or any request that matches no group, goes to the cloud team.
