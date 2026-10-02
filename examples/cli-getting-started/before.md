# Getting Started with Acme Sync

Acme Sync is a super lightweight tool that basically lets you keep your local folders in sync with your Acme Cloud bucket, so you don't have to worry about manually uploading stuff ever again!

## Installation

Before you get started, you'll need to make sure you have Node.js 20+ installed on your machine. Once that's done, you can go ahead and install the CLI globally by running the following command:

```bash
npm install -g @acme/sync-cli
```

After the installation has completed, you should run `acme-sync login` in order to authenticate with your Acme account - this will open up a browser window where you'll be asked to sign in and approve the **Sync Access** permission.

## Configuring your first sync

To set up a sync, you'll want to create a config file called `acme-sync.yaml` in the root of your project. It's important to note that the bucket name must exactly match the one shown in the Acme Console under **Storage > Buckets**, otherwise the sync will fail silently, which can be pretty confusing.

```yaml
bucket: my-team-bucket
local_path: ./assets
direction: push
```

Once your config is ready, simply run `acme-sync start` and the tool will begin watching your folder for changes. Files that have been modified will be uploaded automatically every few seconds.

> Note: Be careful when using `direction: mirror`, since files that are deleted locally will also be removed from the bucket and this cannot be undone!

## Troubleshooting

If you're running into issues, try running `acme-sync doctor`, which checks your setup and points out common problems. You may also want to check out the logs, which are stored in `~/.acme-sync/logs`.
