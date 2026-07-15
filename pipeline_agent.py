"""Zoho-side helper for the Article/Conference pipeline automation.

This script does NOT call the Anthropic API -- the research + drafting step
is done by whatever Claude Code agent invokes this script (using its own
web search, covered by plan usage, not a separate metered API key). This
file only handles the Zoho CRM / Zoho Mail mechanics:

  python pipeline_agent.py list
      Prints pending leads (Article/Conference status, not yet drafted) as JSON.

  python pipeline_agent.py save <lead_id> <to_email> <subject> <body_file>
      Wraps the body (plain text, read from body_file) in the branded
      email-template.local.html, saves it as a Zoho Mail draft (never sends),
      and marks the lead's Outreach_Draft_Created field as "Yes".

Requires in Zoho CRM (added manually in Setup):
- Lead_Status picklist values: "Article", "Conference"
- Lead field: Outreach_Draft_Created (Yes/No picklist)
"""
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "outreach-emailer" / ".env")

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


def fetch_pending_leads(token):
    """Leads sitting in Article/Conference status that haven't been drafted yet."""
    pending = []
    page = 1
    fields = "id,Full_Name,First_Name,Company,Industry,Designation,Email,Lead_Status,Outreach_Draft_Created"
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
            if lead.get("Lead_Status") in ("Article", "Conference") and lead.get(
                "Outreach_Draft_Created"
            ) != "Yes":
                pending.append(
                    {
                        "id": lead["id"],
                        "name": lead.get("Full_Name") or lead.get("First_Name") or "there",
                        "first_name": lead.get("First_Name") or "",
                        "company": lead.get("Company") or "",
                        "industry": lead.get("Industry") or "",
                        "title": lead.get("Designation") or "",
                        "hook": lead.get("Lead_Status"),
                        "email": lead.get("Email") or "",
                    }
                )
        if not resp.json().get("info", {}).get("more_records"):
            break
        page += 1
    return pending


def mark_lead_drafted(token, lead_id):
    resp = requests.put(
        "https://www.zohoapis.com/crm/v2/Leads",
        headers={
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        },
        json={"data": [{"id": lead_id, "Outreach_Draft_Created": "Yes"}]},
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


def cmd_list():
    token = get_zoho_token()
    leads = fetch_pending_leads(token)
    print(json.dumps(leads, indent=2))


def cmd_save(lead_id, to_email, subject, body_file):
    body_text = Path(body_file).read_text(encoding="utf-8")
    token = get_zoho_token()
    save_draft(token, subject, body_text, to_email)
    mark_lead_drafted(token, lead_id)
    print(f"Draft saved and lead {lead_id} marked as drafted.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    if command == "list":
        cmd_list()
    elif command == "save":
        if len(sys.argv) != 6:
            print("Usage: python pipeline_agent.py save <lead_id> <to_email> <subject> <body_file>")
            sys.exit(1)
        cmd_save(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
