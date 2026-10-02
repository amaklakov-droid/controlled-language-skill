# Getting Started with Acme Sync

Acme Sync is a lightweight command-line interface (CLI) tool. It syncs your local folders with your Acme Cloud bucket. You do not have to upload files manually.

## Installation

1. Make sure that your computer has Node.js 20 or later.
2. Install Acme Sync globally with this command:

   ```bash
   npm install -g @acme/sync-cli
   ```

3. To authenticate with your Acme account, run `acme-sync login`. The command opens a browser window.
4. In the browser window, sign in to your Acme account.
5. Approve the **Sync Access** permission.

## Configuring your first sync

> **WARNING:** If you delete local files and must keep their copies in the bucket, do not use `direction: mirror`. With `direction: mirror`, when you delete a file from your local folder, Acme Sync also deletes the file from the bucket. You cannot undo the deletion.

To configure a sync, do these steps:

1. In the root folder of your project, create a configuration file with the name `acme-sync.yaml`.
2. Add the sync settings to the file. For example:

   ```yaml
   bucket: my-team-bucket
   local_path: ./assets
   direction: push
   ```

3. In the Acme Console, find the name of your bucket under **Storage > Buckets**.
4. Make sure that the value of `bucket` is exactly the same as this name. If the names are different, the sync fails without an error message.
5. Run `acme-sync start`. Acme Sync starts to monitor your local folder for changes. It uploads changed files automatically every few seconds.

## Troubleshooting

If you have problems with Acme Sync, run `acme-sync doctor`. This command checks your setup and shows common problems.

You can also examine the log files in `~/.acme-sync/logs`.
