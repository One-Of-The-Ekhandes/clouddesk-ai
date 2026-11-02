---
title: AWS AccessDenied / not authorized to perform an action
category: cloud_access
team: cloud_team
---
Symptoms: "AccessDenied", "is not authorized to perform", "UnauthorizedOperation" from the AWS console, CLI or a deployment.

Steps:
1. Record the exact action and resource ARN from the error message.
2. Check which IAM groups the user belongs to and which policies those groups attach.
3. If a read-access group (dev-readonly, data-analysts) grants the action and fits the user's role, add the user to that group (least privilege).
4. If only dev-deployers or prod-operators grants it, or no group does, escalate to the cloud team with the action, resource and business reason.
Never attach AdministratorAccess to fix a single denied action.
