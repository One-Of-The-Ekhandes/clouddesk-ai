---
title: Emails bouncing or not delivered
category: email
team: service_desk
---
Symptoms: non-delivery report (NDR), emails to an external domain bouncing, messages stuck in the outbox.

Steps:
1. Read the NDR code (for example 550 5.7.1) and the rejecting server.
2. Run a message trace in the Exchange admin centre.
3. If the recipient domain rejects the mail, advise the sender to contact the recipient's IT team; if many domains reject us, escalate to the messaging team.
