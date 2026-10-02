# Rotate the signing secret of a webhook endpoint

Payhub uses webhooks to send payment notifications to your server. Payhub signs each webhook with the signing secret of the webhook endpoint. Your server uses the same signing secret to verify the signature of each webhook.

When you click **Rotate secret**, Payhub makes a new signing secret. Then a 24-hour period starts.

During the 24-hour period:

- Your server can verify webhook signatures with the old signing secret.
- You can click **Revert** to use the old signing secret again.

After the 24-hour period:

- Your server cannot verify webhook signatures with the old signing secret.
- You cannot click **Revert**.

## Rotate the signing secret

> **WARNING:** Do steps 4 to 6 during the 24-hour period after you click **Rotate secret**. After this period, your server cannot verify webhook signatures with the old signing secret. Your server then rejects the payment notifications from Payhub.

1. Go to **Developers** > **Webhooks**.
2. Select the webhook endpoint.
3. Click **Rotate secret**.
   Payhub makes a new signing secret. The 24-hour period starts.
4. Copy the new signing secret.
5. On your server, set the environment variable `PAYHUB_WEBHOOK_SECRET` to the new signing secret.
6. Deploy your server again.

## Use the old signing secret again

If you must use the old signing secret again, do these steps during the 24-hour period:

1. Go to **Developers** > **Webhooks**.
2. Select the webhook endpoint.
3. Click **Revert**.
