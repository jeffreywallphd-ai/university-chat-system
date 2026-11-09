# MTU Assistant user guide

MTU Assistant is a campus assistant for Michigan Technological University. The page itself is labeled Michigan Technological University. You search, and a campus assistant opens with an answer taken from public MTU pages the app has stored.

It does not see your Banweb account, Canvas courses, grades, or personal schedule. If a fact is not on the public pages it has read, the reply is only: **I don't have such information.**

## Start the app

From the project folder in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Leave that window open. In a browser, open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Stop the server with Ctrl+C in that window.

The first start can take a few minutes while campus pages are read in the background. You can search as soon as the page loads. A question about a topic that is still loading gets “I don't have such information.” Ask again after that read finishes.

If this is a brand-new copy of the project, create the environment once:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

No API key is required to ask questions.

## Ask a question

The background is a moving list of upcoming campus events. Clicking an event asks about that event.

1. Type in the search box. The heading is “What do you want to know?” The hint under the box is “Search opens the campus assistant.”
2. Press Enter or Search. The assistant opens at the bottom right, labeled Campus assistant.
3. The reply is the matching section from a stored campus page. A link under the reply opens that page.
4. Ask a follow-up in the box inside the panel. Enter sends. Shift+Enter adds a line.
5. Close the panel with the × button. The search box stays on the page.

The search box and the follow-up box each accept up to 2000 characters. Wait until the current reply finishes before sending another.

## Memory

The assistant remembers the recent turns in this browser tab only. A short follow-up such as “what about Friday?” can stay on the previous topic. Refreshing or closing the page clears that conversation. Nothing from the chat is saved on the server, and there is no profile that lasts across visits.

## Narrow the topic

The buttons in the header limit which stored pages are searched:

| Button | What it searches |
|---|---|
| All | Every stored page |
| News | MTU news |
| Events | The events calendar |
| Library | Library pages |
| Tutoring | Learning-center pages |
| Registration | Registrar pages |
| Housing | Residential Living pages |
| Career | Career Services pages |
| Campus | IT help, well-being, public safety, the dean of students, financial aid, tuition, and recreation |

All is selected when you first open the page. Click another topic before you search if you want a narrower answer.

## What a reply looks like

The reply is text from the page that matched, not a rewritten paragraph. Hours appear as the schedule on that page. A date question uses the date lines on that page. If the pages do not contain the fact, the only reply is “I don't have such information.”

Use the link under the message when you need the original page. The page is the authority if you want the surrounding context.

## What it can answer

Questions about public information it has stored, for example:

- Library hours, and Velodrome Coffee Company hours on the library hours page
- The Career Fair date on the Career Services career-fair page
- Upcoming events on the Michigan Tech events calendar
- Housing on the Residential Living pages
- Registration, tutoring, news, financial aid, and tuition when those pages were collected

## What it cannot answer

- Your class schedule, bill, holds, grades, password, or anything behind an MTU login
- A page that has not been collected, or a site the app does not read
- A fact that is not in the stored section. It does not guess.

Name the office or building when you can. “Library hours on Saturday” works better than “hours?”

## If something goes wrong

**The page does not load.** The server window must still be running, and the address must be [http://127.0.0.1:8000](http://127.0.0.1:8000).

**“I don't have such information.”** The stored pages do not contain an answer, or that topic is still loading after a restart. Check [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health). `chunks` should be greater than 0. Try All if a topic button is hiding the page you need.

**“Something went wrong while answering.”** Ask again. If the page itself fails to load, the server is not running.

**An answer is a schedule or a date you did not expect.** Open the source link under the reply. The assistant copies a section from that page after checking the page again. If the page and the reply disagree, use the page.

**You changed the code and the page looks the same.** Stop the server and start it again. It does not reload code by itself. Refresh the browser after the restart.

## Running it for other people

Bind the server only where you intend people to reach it. Anyone who can open the site can ask questions. They cannot trigger a full reread of campus pages unless they have the admin key. A normal question does recheck the one page it is about to use, and updates the stored copy if that page changed.

To reread every configured source:

```powershell
curl.exe -X POST http://127.0.0.1:8000/ingest -H "X-API-Key: YOUR_KEY"
```

Replace `YOUR_KEY` with `ADMIN_API_KEY` from `.env`. One source at a time:

```powershell
curl.exe -X POST http://127.0.0.1:8000/ingest/library -H "X-API-Key: YOUR_KEY"
```

Source names are `mtu-news`, `mtu-events`, `library`, `tutoring`, `registration`, `housing`, `career`, and `campus`.

Keep `.env` on your machine. Do not publish it. How the pieces fit together is in [TECHNICAL.md](TECHNICAL.md).
