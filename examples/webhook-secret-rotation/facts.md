# Input: facts from the user

The user gave these facts and asked for a strict (Level 3) procedure. The
text will be machine-translated into 12 languages.

<!-- controlled-language: off -->
> Write a short procedure for our admin guide: how to rotate the webhook
> signing secret in Payhub. Facts: go to Developers > Webhooks, choose the
> endpoint, click Rotate secret. The old secret keeps working for 24 hours,
> then it stops. You have to update the secret in your server env var
> PAYHUB_WEBHOOK_SECRET and redeploy within those 24h, otherwise webhook
> signature verification fails and payment notifications get rejected. You
> can roll back by clicking 'Revert' only during the 24h window.
<!-- controlled-language: on -->
