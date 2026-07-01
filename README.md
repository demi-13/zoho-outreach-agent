# AI Outreach Agent

An AI-powered outreach assistant that finds a real, recent article or upcoming conference relevant to a prospect's world and drafts a casual 1-2 sentence email — signed by you. Saves the draft straight to Zoho Mail (or a local file as fallback). Never sends. Never deletes.

---

## What It Does

1. You give it a prospect's name, company, and industry
2. It asks: **Article or conference?**
3. It searches the web for something real and recent in their space
4. It writes a short, casual email with the link — the way you'd text a colleague something cool
5. It saves the draft to your Zoho Mail drafts folder, ready to review and send

---

## Stack

- **Claude** (claude-opus-4-8 with web search) — email drafting + web research
- **Zoho CRM** — prospect lookup via OAuth2
- **Zoho Mail API** — draft saving (never sends)
- **PowerShell** — token refresh and API calls
- **Python** — CLI runner

---

## How to Run It

### Option 1 — Python CLI

```bash
python run.py
```

Or pass everything inline:

```bash
python run.py "Sarah Chen" "MedTech Inc" "medical devices"
```

### Option 2 — Claude Code interactive

Open Claude Code from this folder and say:

```
Run the outreach agent for Sarah Chen at MedTech Inc in medical devices.
```

---

## What You'll Get

```
Subject: FDA's new draft guidance on 3D printed medical devices

FDA just dropped draft guidance on additive manufacturing for medical devices, https://fda.gov/..., would love to work on something like this together.

With gratitude, [YOUR_ALIAS]
```

Short. Real link. No fluff. Ready to send.

---

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   ANTHROPIC_API_KEY=
   ZOHO_CLIENT_ID=
   ZOHO_CLIENT_SECRET=
   ZOHO_REFRESH_TOKEN=
   ```
3. Edit `signature.html` with your name, title, logo, and contact info
4. Edit `AGENT.md` to replace `[YOUR_NAME]`, `[YOUR_COMPANY]`, etc. with your details
5. Run `python run.py`

### Zoho OAuth Scopes Required

```
ZohoCRM.modules.ALL ZohoMail.accounts.READ ZohoMail.messages.ALL
```

---

## Files

```
ai-outreach-agent/
├── AGENT.md          ← agent instructions for Claude
├── run.py            ← Python CLI runner
├── signature.html    ← HTML email signature template
├── .env.example      ← credentials template (copy to .env)
├── README.md         ← this file
└── drafts/           ← local draft fallback (auto-created)
```

---

## Hard Limits (built into the agent)

- Never sends email
- Never deletes anything
- Only saves to Zoho Mail as a draft, or locally as a `.txt` file
