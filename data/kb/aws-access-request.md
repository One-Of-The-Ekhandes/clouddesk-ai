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

Who approves:
- dev-readonly and data-analysts (read access): the service desk adds the user to the group.
- dev-deployers (deploy rights) and prod-operators (production): the cloud team approves and makes the change.
- Any request that matches no group goes to the cloud team.
