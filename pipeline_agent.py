"""Zoho-side helper for the Article/Conference pipeline automation.

This script does NOT call the Anthropic API -- the research + drafting step
is done by whatever Claude Code agent invokes this script (using its own
web search, covered by plan usage, not a separate metered API key). This
file only handles the Zoho CRM / Zoho Mail mechanics:

  python pipeline_agent.py list
      Prints pending leads as JSON: leads currently in Article status without
      an Article draft yet, plus leads currently in Conference status without
      a Conference draft yet. Article and Conference are tracked separately,
      so a lead can qualify for both across its lifecycle -- e.g. drafted for
      Article, later moved to Conference status, drafted again for that.

  python pipeline_agent.py save <lead_id> <to_email> <subject> <body_file> <hook>
      Wraps the body (plain text, read from body_file) in the branded
      email-template.local.html, saves it as a Zoho Mail draft (never sends),
      and marks the lead's hook-specific field ("Article_Draft_Created" or
      "Conference_Draft_Created", matching <hook>) as "Yes".

  python pipeline_agent.py notify <subject> <description_file>
      Creates a Zoho CRM Task assigned to [YOUR_ALIAS] (owner id from
      OWNER_ZOHO_USER_ID) so she knows to check Zoho Mail drafts. Call once
      per run after the save loop, summarizing what happened.

Requires in Zoho CRM (added manually in Setup):
- Lead_Status picklist values: "Article", "Conference"
- Lead fields: Article_Draft_Created, Conference_Draft_Created (Yes/No picklists)
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

TEMPLATE_PATH = Path(__file__).parent / "email-template.local.html"


def get_zoho_token():
    resp = requests.post(
        "https://accounts.zoho.com/oauth/v2/token",
        params={
            "grant_type": "refresh_token",
            "client_id": os.getenv("ZOHO_CLIENT_ID"),
            "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
            "refresh_token": os.getenv("ZOHO_REFRESH_TOKEN"),
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


DRAFT_FIELD_BY_HOOK = {
    "Article": "Article_Draft_Created",
    "Conference": "Conference_Draft_Created",
}


def fetch_pending_leads(token):
    """Leads sitting in Article/Conference status that haven't been drafted for
    their *current* hook yet. Article and Conference each have their own
    Yes/No field, so a lead already drafted for Article still qualifies once
    it's later moved to Conference status, and vice versa."""
    pending = []
    page = 1
    fields = (
        "id,Full_Name,First_Name,Company,Industry,Designation,Email,Lead_Status,"
        "Article_Draft_Created,Conference_Draft_Created"
    )
    while True:
        resp = requests.get(
            "https://www.zohoapis.com/crm/v2/Leads",
            headers={"Authorization": f"Zoho-oauthtoken {token}"},
            params={"fields": fields, "per_page": 200, "page": page},
        )
        if resp.status_code == 204:
            break
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            break
        for lead in data:
            hook = lead.get("Lead_Status")
            draft_field = DRAFT_FIELD_BY_HOOK.get(hook)
            if draft_field and lead.get(draft_field) != "Yes":
                pending.append(
                    {
                        "id": lead["id"],
                        "name": lead.get("Full_Name") or lead.get("First_Name") or "there",
                        "first_name": lead.get("First_Name") or "",
                        "company": lead.get("Company") or "",
                        "industry": lead.get("Industry") or "",
                        "title": lead.get("Designation") or "",
                        "hook": hook,
                        "email": lead.get("Email") or "",
                    }
                )
        if not resp.json().get("info", {}).get("more_records"):
            break
        page += 1
    return pending


def mark_lead_drafted(token, lead_id, hook):
    draft_field = DRAFT_FIELD_BY_HOOK.get(hook)
    if not draft_field:
        raise ValueError(f"Unknown hook '{hook}', expected 'Article' or 'Conference'")
    resp = requests.put(
        "https://www.zohoapis.com/crm/v2/Leads",
        headers={
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        },
        json={"data": [{"id": lead_id, draft_field: "Yes"}]},
    )
    resp.raise_for_status()


def wrap_in_template(body_text):
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    body_html = body_text.replace("\n\n", "<br><br>").replace("\n", "<br>")
    return template.replace("{{BODY}}", body_html)


def save_draft(token, subject, body_text, to_address):
    accounts = requests.get(
        "https://mail.zoho.com/api/accounts",
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
    )
    accounts.raise_for_status()
    account_id = accounts.json()["data"][0]["accountId"]

    full_html = wrap_in_template(body_text)

    resp = requests.post(
        f"https://mail.zoho.com/api/accounts/{account_id}/messages",
        headers={
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        data=json.dumps(
            {
                "fromAddress": os.getenv("FROM_ADDRESS", ""),
                "toAddress": to_address or "",
                "subject": subject,
                "content": full_html,
                "mailFormat": "html",
                "mode": "draft",
            }
        ).encode("utf-8"),
    )
    resp.raise_for_status()


def create_task(token, subject, description):
    resp = requests.post(
        "https://www.zohoapis.com/crm/v2/Tasks",
        headers={
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(
            {
                "data": [
                    {
                        "Subject": subject,
                        "Description": description,
                        "Due_Date": date.today().isoformat(),
                        "Status": "Not Started",
                        "Priority": "High",
                        "Owner": {"id": os.getenv("OWNER_ZOHO_USER_ID")},
                        "Send_Notification_Email": True,
                    }
                ]
            }
        ).encode("utf-8"),
    )
    resp.raise_for_status()
    return resp.json()


def cmd_list():
    token = get_zoho_token()
    leads = fetch_pending_leads(token)
    print(json.dumps(leads, indent=2))


def cmd_save(lead_id, to_email, subject, body_file, hook):
    body_text = Path(body_file).read_text(encoding="utf-8")
    token = get_zoho_token()
    save_draft(token, subject, body_text, to_email)
    mark_lead_drafted(token, lead_id, hook)
    print(f"Draft saved and lead {lead_id} marked as drafted for {hook}.")


def cmd_notify(subject, description_file):
    description = Path(description_file).read_text(encoding="utf-8")
    token = get_zoho_token()
    create_task(token, subject, description)
    print("Notification task created for [YOUR_ALIAS].")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    if command == "list":
        cmd_list()
    elif command == "save":
        if len(sys.argv) != 7:
            print("Usage: python pipeline_agent.py save <lead_id> <to_email> <subject> <body_file> <hook: Article|Conference>")
            sys.exit(1)
        cmd_save(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    elif command == "notify":
        if len(sys.argv) != 4:
            print("Usage: python pipeline_agent.py notify <subject> <description_file>")
            sys.exit(1)
        cmd_notify(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
