import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

SYSTEM_PROMPT = """You are a personal outreach assistant. Your user is a fractional R&D consultant specializing in plastic materials, polymer testing, resin-based 3D printing, failure analysis, and chemical formulation. Clients are in manufacturing, medical devices, fertility science, biotech, and advanced materials.

Your job is to find one specific article, conference, grant opportunity, or industry event that is directly relevant to the prospect's work AND something your user could realistically help with. Share it like a colleague texting something cool they just found.

Rules:
- 1-2 sentences only
- Include the real URL
- End with "thought of you" or "would love to work on something like this together"
- No fluff, no intro, no sales language
- No em dashes or double hyphens
- Plain text only, no HTML or citation tags
- Do not explain your reasoning or introduce the email, output begins immediately
- Return in this exact format, nothing before or after:

Subject: [one sharp, specific subject line]

[email body]

With gratitude, [YOUR_ALIAS]"""


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
    return resp.json().get("access_token")


def save_to_zoho_mail(subject, body, to_address=""):
    token = get_zoho_token()
    accounts = requests.get(
        "https://mail.zoho.com/api/accounts",
        headers={"Authorization": f"Zoho-oauthtoken {token}"},
    )
    accounts.raise_for_status()
    account_id = accounts.json()["data"][0]["accountId"]

    resp = requests.post(
        f"https://mail.zoho.com/api/accounts/{account_id}/messages",
        headers={
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json",
        },
        json={
            "fromAddress": os.getenv("FROM_ADDRESS", ""),
            "toAddress": to_address,
            "subject": subject,
            "content": body,
            "mailFormat": "html",
            "mode": "draft",
        },
    )
    resp.raise_for_status()


def save_locally(prospect_name, subject, body):
    drafts_dir = Path(__file__).parent / "drafts"
    drafts_dir.mkdir(exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", prospect_name)
    date = datetime.now().strftime("%Y-%m-%d")
    out_file = drafts_dir / f"{date}_{safe_name}.txt"
    out_file.write_text(f"Subject: {subject}\n\n{body}\n", encoding="utf-8")
    return out_file


def generate_email(name, company, industry, title=""):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    hook = input("Article or conference? ").strip().lower()
    if "conf" in hook:
        search_hint = "Search for a real upcoming conference or trade event relevant to their industry and materials/R&D."
    else:
        search_hint = "Search for a real recent article, study, or regulatory update relevant to their industry and materials/R&D."

    user_prompt = f"""Research this prospect and draft a personalized outreach email.

Prospect:
- Name: {name}
{f"- Title: {title}" if title else ""}
- Company: {company}
- Industry: {industry}

{search_hint} Include the real URL naturally in the email body.

Return only the Subject line, then a blank line, then the email body. Nothing else."""

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = "".join(b.text for b in response.content if b.type == "text").strip()
    match = re.match(r"Subject:\s*(.+?)\n\n(.*)", raw, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "", raw


def main():
    print("\n--- AI Outreach Agent ---\n")

    if len(sys.argv) == 4:
        name, company, industry = sys.argv[1], sys.argv[2], sys.argv[3]
        title = ""
    else:
        name     = input("Prospect name:     ").strip()
        title    = input("Title (optional):  ").strip()
        company  = input("Company:           ").strip()
        industry = input("Industry:          ").strip()

    if not name or not company or not industry:
        print("Name, company, and industry are required.")
        sys.exit(1)

    print("\nSearching and drafting...")
    subject, body = generate_email(name, company, industry, title)

    print("\n" + "=" * 50)
    print(f"Subject: {subject}\n")
    print(body)
    print("=" * 50 + "\n")

    try:
        save_to_zoho_mail(subject, body)
        print("Saved to Zoho Mail drafts.")
    except Exception as e:
        out_file = save_locally(name, subject, body)
        print(f"Zoho Mail unavailable ({type(e).__name__}) -- saved locally: {out_file}")


if __name__ == "__main__":
    main()
