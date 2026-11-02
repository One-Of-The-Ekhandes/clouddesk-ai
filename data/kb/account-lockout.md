---
title: Account locked out (Active Directory / Entra ID)
category: account_access
team: service_desk
---
Symptoms: user cannot sign in, sees "account is locked" or repeated password prompts, often right after a password change.

Steps:
1. Verify the user's identity using the approved method before any change.
2. Check account status and lockout source (Event ID 4740 on the domain controller, or the Entra ID sign-in logs).
3. Unlock the account.
4. Find the device sending the old password: phone mail apps, mapped drives, saved Windows Credential Manager entries, scheduled tasks.
5. Remove or update the stale credential, then confirm a clean sign-in.

Escalate to the security team if the lockouts come from an unknown IP address or country.
