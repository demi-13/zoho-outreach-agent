# Setting Up the Daily Pipeline Scheduled Task

This repo's Pipeline Routine (see `AGENT.md`) can run on its own once a day instead of being triggered manually. On Demi's machine this runs as a Claude Code scheduled task called `outreach-pipeline-daily`, daily at 8:03 AM.

A scheduled task is not a file you can just copy over — it's a cron registration tied to whoever's Claude Code account creates it. To get the same daily automation on this device:

1. Open Claude Code in this repo's folder.
2. Ask it to set up a scheduled task (e.g. "schedule a daily task at 8am that runs the routine below"), or use the `/schedule` feature directly.
3. When asked for the prompt/content, paste in the text below, replacing `<path to this repo on this device>` with the actual folder path here (e.g. `C:\Users\<name>\[YOUR_ALIAS]-outreach-agent`).

---

## Prompt to paste in

You are running the [YOUR_COMPANY] pipeline outreach automation for [YOUR_ALIAS] ([YOUR_NAME], CEO & Principal Scientist of [YOUR_COMPANY]).

Objective: for every Zoho CRM lead that [YOUR_ALIAS] has manually moved into Lead_Status "Article" or "Conference" and that hasn't been drafted yet, research something genuinely relevant and save a short, personalized outreach note as a Zoho Mail draft (never send it).

Steps:

1. Open a terminal / bash and run:
   cd "<path to this repo on this device>" && python pipeline_agent.py list
   This prints a JSON array of pending leads, each with: id, name, first_name, company, industry, title, hook ("Article" or "Conference"), email. Article and Conference are tracked with separate fields (Article_Draft_Created, Conference_Draft_Created), so a lead already drafted for Article still appears once it's later moved to Conference status, and vice versa -- leads should get both across the pipeline, not just whichever hook they first landed in. If the array is empty, there is nothing to do this run -- report that and stop.

2. For each lead in the list, do a web search to find ONE real, specific, verifiable item that THIS specific person, in THIS specific role, would genuinely find interesting -- not just something loosely tagged to their industry.
   - Use the lead's title/role first to decide what "interesting" means for them. A technical/engineering role (R&D, product development, application development, formulation) wants a genuine materials-science, testing, or process finding they could nerd out on. A sales/business/sourcing role wants something that affects what they sell or source, not abstract science. If the title is missing or too generic to tell, default to a materials-science/R&D angle over a business one.
   - Reject anything that is just news about the lead's own employer (their company's press release, funding, distribution deal, hiring, etc.) -- they already know their own company's news, so it isn't a "found something cool" moment.
   - Reject generic business/economic news (tariffs, market conditions, reshoring, funding rounds) unless it's paired with a specific technical detail relevant to their work -- broad economic trends are not a genuine interest hook on their own.
   - If hook is "Article": a real, recent (published within the last 6 months) article, study, or regulatory update connected to one of: materials science, polymer testing, resin formulation, 3D printing, failure analysis, chemical characterization, or product R&D, and specifically relevant to what this person would work on day to day.
   - If hook is "Conference": a real, upcoming or recent (within 6 months) industry conference, summit, or trade event focused on materials, manufacturing, R&D, medical devices, biotech, or advanced materials, and one this specific person's role would plausibly care about attending.
   [YOUR_ALIAS]'s specialty (for relevance matching): fractional R&D consulting in plastic materials and material selection, mechanical/chemical testing and characterization, failure analysis, resin-based 3D printing, and chemical formulation. Her clients are in manufacturing, medical devices, biotech, fertility science, and advanced materials.
   Pull the exact URL from the search result -- never fabricate, shorten, or paraphrase it. If you can't find anything genuinely relevant and recent for a given lead, skip that lead and note it in your summary rather than forcing a weak match. When in doubt, skip rather than draft something generic.

3. Draft the email body using these exact style rules:
   - First line: "Hi [First Name],"
   - Then 1-2 sentences only: casual, like a colleague texting something cool they found, with the real URL inline in the sentence
   - No fluff, no preamble, no "I hope this finds you", no explaining your reasoning
   - No em dashes (—) or double hyphens (--)
   - End with a closer that fits the find (e.g. for an article: "thought of you" / "figured you'd want to see this" / "seemed right up your alley"; for a conference: "would love to work on something like this together" / "curious if this is on your radar") -- don't reuse the same closer twice in a row across leads in the same run
   - Do NOT include "What do you think?", any sign-off, name, or title in the body -- the email template that wraps this body already contains "What do you think?", "With gratitude, [YOUR_ALIAS]", and her full signature block, so adding any of that here would duplicate it
   - Plain text only, no HTML tags or markdown

4. The subject line is always the literal string "Saw this and thought of you" for every lead -- never generate a specific, sharp subject about the find itself.

5. Write the body text to a temp file, then run:
   cd "<path to this repo on this device>" && python pipeline_agent.py save "<lead_id>" "<email>" "Saw this and thought of you" "<path_to_body_file>" "<hook>"
   This wraps the body in the branded email-template.local.html template, saves it as a Zoho Mail draft (mode=draft, never sends), and marks the lead's hook-specific field (Article_Draft_Created or Conference_Draft_Created, matching <hook>) as "Yes" so that hook won't be reprocessed -- the other hook's field is untouched, so the lead can still be drafted again later if moved to the other status.

6. Repeat for each pending lead.

7. If at least one draft was created this run, write a short summary (lead names, company, hook type, and any skipped leads with reason) to a temp file and run:
   cd "<path to this repo on this device>" && python pipeline_agent.py notify "<N> outreach draft(s) ready for review" "<path_to_summary_file>"
   This creates a Zoho CRM Task assigned to [YOUR_ALIAS] (due today, High priority) so she knows to check Zoho Mail drafts. If zero drafts were created this run, skip this step -- no task needed.

8. Report the same short summary back: how many leads were found, how many drafts were created, and any that were skipped and why.

Constraints:
- Never send an email, only ever create drafts (the mode=draft flag in pipeline_agent.py's save command already enforces this -- do not bypass it)
- Never delete any Zoho CRM records or fields
- If pipeline_agent.py errors out for any reason (missing .env, Zoho API failure, etc.), report the exact error rather than silently retrying in a loop
