# [YOUR_ALIAS] Outreach Agent

An AI-powered outreach assistant that finds a real, recent article or upcoming conference relevant to a prospect's world and drafts a casual 1-2 sentence email, signed by [YOUR_ALIAS]. Saves the draft straight to Zoho Mail (or a local file as fallback). Never sends. Never deletes.

---

## The Problem

Warm, personalized outreach is what makes a fractional R&D consulting relationship work, but it doesn't scale manually. Finding one genuinely relevant, recent article or conference for a specific prospect takes real research time. Generic mail-merge templates read as exactly that, and prospects can tell.

There's a second version of this problem inside the CRM. Leads sitting in Zoho CRM under "Article" or "Conference" status need that same personal-touch research applied every day as new leads land there. Doing that research by hand each morning isn't realistic.

---

## What It Does

**On demand:**
1. You give it a prospect's name, company, and industry
2. It asks: **Article or conference?**
3. It searches the web for something real and recent in their space
4. It writes a short, casual email with the link, the way you'd text a colleague something cool
5. It saves the draft to the Zoho Mail drafts folder, ready to review and send

**On a schedule:** a separate pipeline routine picks up every lead sitting in Zoho CRM `Lead_Status` "Article" or "Conference." It researches something specific to that person's role, then drafts and saves outreach for each one automatically. See the **Pipeline Routine** section of `AGENT.md`.

---

## How It Works

```
Zoho CRM (Lead_Status: Article / Conference)
        │  pipeline_agent.py list
        ▼
  Claude Code agent (web search, no metered API)
        │  finds one real, recent, role-relevant article or conference
        ▼
  Drafted email (branded HTML template, "Hi [Name]," + 1-2 sentences + real URL)
        │  pipeline_agent.py save
        ▼
  Zoho Mail draft (never sent) + Zoho CRM Task notification to [YOUR_ALIAS]
```

The on-demand flow follows the same shape, triggered by `/outreach` instead of a scheduled `list` call.

---

## Technical Decisions

- **Claude Code as the agent runtime, not a direct Anthropic API integration.** Web search runs on the Claude Code plan instead of a separately metered API call. The same agent doubles as a schedulable routine: `/outreach` for one-off runs, a daily scheduled task for the pipeline. No extra orchestration code needed.
- **Draft-only, never-send by design.** Every Zoho Mail API call hard-codes `mode: "draft"`, and the agent instructions explicitly forbid sending or deleting anything. A consulting relationship depends on a human reviewing the note before it reaches a prospect's inbox. The agent's job stops at producing a good draft.
- **Article and Conference tracked as two separate fields per lead**, not one shared "already drafted" flag. Leads move between statuses over their lifecycle. A lead already drafted for Article can still qualify for a fresh Conference draft later, and vice versa, without either hook getting skipped or duplicated.
- **PowerShell for the interactive flow, Python for the batch flow.** Each matches the runtime it actually executes in. Claude Code drives PowerShell directly for one-off `/outreach` runs. The unattended daily pipeline needs a real, testable script (`pipeline_agent.py`) it can call without a human in the loop.

---

## Impact

- Runs unattended once a day via a scheduled task, turning CRM stage changes into ready-to-review drafts with no manual triggering.
- Each run ends in a single Zoho CRM Task summarizing what was drafted and what was skipped, and why. Review is a five-minute check instead of a research project.
- The never-send, never-delete constraints mean the automation can run fully unattended. There's no risk of an unreviewed email leaving the account.

---

## What's Next

- Feed new leads from the [LinkedIn Lead Scoring + CRM Automation](https://github.com/demi-13/LinkedIn-Connection-Scorer) project directly into this pipeline, instead of requiring a manual `Lead_Status` change to Article or Conference first.
- Track draft-to-send conversion (how many generated drafts actually get sent) to measure whether the hooks are landing, not just whether they're getting generated.
- Extend the pipeline beyond the Article/Conference hooks as new outreach triggers get identified.

---

## Built With

Claude Code (agent runtime + web search), Zoho CRM API, Zoho Mail API, PowerShell, Python (`requests`, `python-dotenv`)

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
