# [YOUR_ALIAS] Outreach Agent

An AI-powered outreach assistant that finds a real, recent article or upcoming conference relevant to a prospect's world and drafts a casual 1-2 sentence email, signed by [YOUR_ALIAS]. Saves the draft straight to Zoho Mail (or a local file as fallback). Never sends. Never deletes.

---

## What It Does

1. You give it a prospect's name, company, and industry
2. It asks: **Article or conference?**
3. It searches the web for something real and recent in their space
4. It writes a short, casual email with the link — the way you'd text a colleague something cool
5. It saves the draft to the Zoho Mail drafts folder, ready to review and send

There's a second, separate routine for leads already sitting in `Lead_Status` "Article" or "Conference" in Zoho CRM — see the **Pipeline Routine** section of `AGENT.md`.

---

## Stack

- **Claude Code** (with web search) — email drafting + web research, run as an agent routine, not a metered API call
- **Zoho CRM** — prospect lookup via OAuth2
- **Zoho Mail API** — draft saving (never sends)
- **PowerShell** — token refresh and API calls
- **Python** (`pipeline_agent.py`) — Zoho CRM/Mail mechanics for the batch pipeline routine only

---

## How to Run It

Open Claude Code from this folder and run:

```
/outreach
```

Or say inline:

```
Run the outreach agent for Sarah Chen at MedTech Inc in medical devices.
```

For the batch Article/Conference pipeline routine, see `AGENT.md`.

---

## What You'll Get

```
Subject: Saw this and thought of you

Hi Sarah,

FDA just dropped draft guidance on additive manufacturing for medical devices, https://fda.gov/..., would love to work on something like this together.

What do you think?

With gratitude,
[YOUR_ALIAS]
```

Short. Real link. No fluff. Ready to send.

---

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   ZOHO_CLIENT_ID=
   ZOHO_CLIENT_SECRET=
   ZOHO_REFRESH_TOKEN=
   FROM_ADDRESS=
   ```
3. Run `/outreach` from Claude Code in this folder

### Zoho OAuth Scopes Required

```
ZohoCRM.modules.ALL ZohoMail.accounts.READ ZohoMail.messages.ALL
```

---

## Files

```
[YOUR_ALIAS]-outreach-agent/
├── AGENT.md                        ← agent instructions (outreach flow + pipeline routine)
├── pipeline_agent.py                ← Zoho mechanics for the Article/Conference pipeline routine
├── email-template.local.html        ← branded HTML email template
├── .claude/commands/outreach.md     ← the /outreach slash command
├── zoho_functions/                  ← Zoho-side (Deluge) pipeline stage automation, versioned reference only
├── requirements.txt                 ← Python dependencies
├── .env.example                     ← credentials template (copy to .env)
├── README.md                        ← this file
└── drafts/                          ← local draft fallback (auto-created)
```

---

## Hard Limits (built into the agent)

- Never sends email
- Never deletes anything
- Only saves to Zoho Mail as a draft, or locally as a `.txt` file
