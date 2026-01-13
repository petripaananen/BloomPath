# Jira Webhook Configuration Guide

This guide walks you through setting up a Jira webhook to send issue updates to BloomPath.

## Prerequisites

- Admin access to your Jira project
- BloomPath middleware running (locally or deployed)
- ngrok tunnel running (for local development)

## Step 1: Get Your Webhook URL

### Local Development (with ngrok)
1. Run `.\start_ngrok.ps1` in PowerShell
2. Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok.io`)
3. Your webhook URL will be: `https://abc123.ngrok.io/webhook`

### Production
Use your deployed server URL: `https://your-server.com/webhook`

## Step 2: Configure Jira Webhook

1. Go to your Jira project
2. Click **Project Settings** (gear icon) → **Webhooks**
   - Or navigate to: `https://YOUR-DOMAIN.atlassian.net/plugins/servlet/webhooks`

3. Click **Create a Webhook**

4. Configure the webhook:
   | Field | Value |
   |-------|-------|
   | Name | `BloomPath Growth Trigger` |
   | URL | `https://YOUR-NGROK-URL/webhook` |
   | Secret | *(optional, for security)* |

5. Under **Events**, select:
   - ✅ `Issue` → `updated`

6. Under **JQL Filter** (optional):
   ```
   project = YOUR_PROJECT_KEY
   ```

7. Click **Create**

## Step 3: Test the Webhook

1. Ensure BloomPath middleware is running:
   ```powershell
   cd c:\Users\petri\.gemini\antigravity\BloomPath
   python middleware.py
   ```

2. In Jira, move any issue to **Done** status

3. Check the middleware console for:
   ```
   [issue_updated] Issue: PROJECT-123, Status: Done
   ✅ Triggered growth for PROJECT-123 in UE5
   ```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Webhook not received | Check ngrok is running and URL is correct |
| 401 Unauthorized | Verify webhook secret matches (if configured) |
| Connection refused | Ensure middleware is running on port 5000 |

## Security Notes

> ⚠️ **Important**: ngrok URLs change each time you restart. For production, use a stable deployment or ngrok with a reserved subdomain.
