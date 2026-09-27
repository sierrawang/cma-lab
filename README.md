# Lab: Build a Travel Agent with Claude Managed Agents

**Time:** about 60 minutes

**You'll build:** a travel agent that searches real flights and works out whether to use your points. You will create every file and learn how to build with Claude Managed Agents. We provide code and guidance throughout the process, but remember that your goal is to **learn**, not just complete the task. Happy learning!

| Part | What you'll do |
|---|---|
| [Before you start](#before-you-start) | Get your environment set up |
| [Milestone 1](#milestone-1-chat-with-your-agent) | Chat with your agent |
| [Milestone 2](#milestone-2-find-real-flights) | Find real flights (MCP + vault) |
| [Milestone 3](#milestone-3-use-my-points) | Use your points (skill + custom tool) |
| [Check your understanding](#check-your-understanding) | Five short questions |
| [Extensions](#extensions-optional) | Booking, hotels, memory, price alerts, a web app |

Each step ends with "You know it worked when…" so you can check your progress as you go.

---

## Before you start

### A. Python 3.10 or newer

Check what you have:

```bash
python3 --version
```

If it says 3.10 or higher, skip ahead. If not, install it:

<details>
<summary>Mac</summary>

Install [Homebrew](https://brew.sh) if you don't have it, then:

```bash
brew install python@3.12
```

Check it worked:

```bash
python3.12 --version
```

Use `python3.12` wherever this lab says `python3`.
</details>

<details>
<summary>Linux or Windows</summary>

On Windows, first install WSL (open PowerShell as administrator, run `wsl --install`, and restart), then do everything in this lab inside the Ubuntu terminal. Then:

```bash
sudo apt update && sudo apt install -y python3 python3-venv
```

Check it worked:

```bash
python3 --version
```
</details>

### B. Install ant, Anthropic's command-line tool

Click your computer:

<details>
<summary>Mac</summary>

```bash
brew install anthropics/tap/ant
```

The first install can take a few minutes.
</details>

<details>
<summary>Linux or Windows</summary>

Find the latest version number at [github.com/anthropics/anthropic-cli/releases](https://github.com/anthropics/anthropic-cli/releases) (for example 1.35.0). Put it on the first line, then run both lines together:

```bash
VERSION=1.35.0
curl -fsSL "https://github.com/anthropics/anthropic-cli/releases/download/v${VERSION}/ant_${VERSION}_linux_$(uname -m | sed -e s/x86_64/amd64/ -e s/aarch64/arm64/).tar.gz" | sudo tar -xz -C /usr/local/bin ant
```
</details>

Check it worked:

```bash
ant --version
```

✅ **You know it worked when** it prints 1.30.0 or newer.

### C. Make your project folder

Create the folder and go into it:

```bash
mkdir travel-agent && cd travel-agent
```

Create a Python environment for the project and turn it on:

```bash
python3 -m venv .venv && source .venv/bin/activate
```

Install Anthropic's Python library:

```bash
pip install anthropic
```

### D. Your Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign in (or create an account).
2. Open **Settings → API keys** and click **Create key**.
3. Name it `travel-agent-lab`.
4. Copy the key (it starts with `sk-ant-`). In your `travel-agent` folder, create a file named `.env` and paste it in like this:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### E. Your SerpApi API key

SerpApi gives your agent live Google Flights results. It's free and takes about 2 minutes.

1. Go to [serpapi.com/users/sign_up](https://serpapi.com/users/sign_up) and sign up with Google, GitHub, or email. You'll verify an email address and a phone number. No credit card.
2. Choose the **Free** plan (250 searches a month; this lab uses about 20).
3. Open [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key), copy your **Private API Key**, and add it to `.env` on a new line:

```
SERPAPI_API_KEY=...
```

### F. Load Your Keys

In the `travel-agent` folder, you should now have a file named `.env` with your two keys:
```
ANTHROPIC_API_KEY=sk-ant-...
SERPAPI_API_KEY=...
```

Load them into your terminal:

```bash
set -a; source .env; set +a
```

> **In every new terminal window**, go to your `travel-agent` folder and run this line first:

```bash
source .venv/bin/activate && set -a && source .env && set +a
```

Check it worked:

```bash
ant auth status
```

✅ **You know it worked when** it shows your key (starting `sk-ant-`) as the active credential.

---

## Milestone 1: Chat with your agent

**Goal:** describe the agent and its container, upload them, and chat with the agent in your terminal.

At the end of this milestone, your folder looks like this:

```
travel-agent/
├── .env
├── agents/
│   └── travel-agent.md          ← new
├── environments/
│   └── travel-env.yaml          ← new
├── claude-lock.json             ← made by ant apply
├── travel_agent.py              ← new
└── chat.py                      ← new
```

### 1.1 Describe the agent

Create `agents/travel-agent.md`. The part between the `---` lines is the agent's settings. Everything below it is the **system prompt**: your instructions to Claude.

```markdown
---
name: Travel Agent
model: claude-opus-5
tools:
  - type: agent_toolset_20260401
---
You are the travel agent inside My Travel App. You help travelers plan and book trips.
Keep every reply to 1-3 short sentences, in plain text. No Markdown.
Give a short reason for each recommendation.
```

`agent_toolset_20260401` is Anthropic's built-in toolset (bash, files, web search); the date is its version. Feel free to change the prompt.

### 1.2 Describe its container

Create `environments/travel-env.yaml`. **Replace `yourname` with your name**, since environment names must be unique in your workspace.

```yaml
name: travel-env-yourname
config:
  type: cloud
  networking:
    type: unrestricted
```

### 1.3 Upload both

First, preview what will happen. Nothing changes yet:

```bash
ant apply --dry-run agents/travel-agent.md environments/travel-env.yaml
```

Then upload them, and answer `y` when it asks:

```bash
ant apply agents/travel-agent.md environments/travel-env.yaml
```

✅ **You know it worked when** you see `created` next to both files, and a new file, `claude-lock.json`, appears. It holds your agent's ID (`agent_…`) and your environment's ID (`env_…`).

### 1.4 Write the code that talks to your agent

Create `travel_agent.py`. Most of it is given; **you write `run_turn()`** in the next step.

```python
"""Talks to your Travel Agent on Claude Managed Agents."""
import json

import anthropic

client = anthropic.Anthropic()

# The IDs that `ant apply` saved
lock = json.load(open("claude-lock.json"))["resources"]
AGENT_ID = lock["./agents/travel-agent.md"]["id"]
ENV_ID = lock["./environments/travel-env.yaml"]["id"]


def start_session():
    session = client.beta.sessions.create(agent=AGENT_ID, environment_id=ENV_ID)
    return session.id


def send_message(session_id, text):
    client.beta.sessions.events.send(
        session_id=session_id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": text}]}],
    )


def run_turn(session_id, text):
    pass  # you'll write this in 1.5
```

### 1.5 Write the event loop

Replace `pass` in `run_turn()` with a loop that:

1. opens the event stream: `with client.beta.sessions.events.stream(session_id=session_id) as stream:`
2. **then** sends the message: `send_message(session_id, text)`
3. goes through each `event` in the stream:
   - `agent.message`: print the agent's reply, `event.content[0].text`, labeled so it stands out: `print(f"\nagent › {event.content[0].text}")`
   - `agent.tool_use` or `agent.mcp_tool_use`: print `f"  ({event.name}…)"`, so you can see what the agent is doing
   - `session.status_idle`: the agent is done, so `break`

<details>
<summary>Stuck? Show the loop.</summary>

```python
def run_turn(session_id, text):
    with client.beta.sessions.events.stream(session_id=session_id) as stream:
        send_message(session_id, text)
        for event in stream:
            if event.type == "agent.message":
                print(f"\nagent › {event.content[0].text}")
            elif event.type in ("agent.tool_use", "agent.mcp_tool_use"):
                print(f"  ({event.name}…)")
            elif event.type == "session.status_idle":
                break
```
</details>

### 1.6 Make the chat app

Create `chat.py`:

```python
"""My Travel App, in the terminal."""
from travel_agent import run_turn, start_session

print("Travel Agent. Type a message, or press Enter on an empty line to quit.")
session_id = start_session()
while True:
    text = input("\nyou › ").strip()
    if not text:
        break
    run_turn(session_id, text)
```

Run it:

```bash
python chat.py
```

Type *Hi! I'm thinking about a trip to Maui.*

✅ **You know it worked when**:
- the agent replies within about 30 seconds, and
- the [Sessions page in the Console](https://platform.claude.com/workspaces/default/sessions) (**Managed Agents → Sessions**) lists your session. Click it to see the conversation.

> **Try this:** ask *How much is a flight from SFO to Maui?* Your agent has no flight data yet. Does it guess? Milestone 2 fixes that.

---

## Milestone 2: Find real flights

**Goal:** connect your agent to SerpApi's MCP server, so it can search live Google Flights prices, without your key ever entering the container.

At the end of this milestone, your folder looks like this:

```
travel-agent/
├── .env
├── agents/
│   └── travel-agent.md          ← updated
├── environments/
│   └── travel-env.yaml
├── claude-lock.json
├── make_vault.py                ← new
├── vault.json                   ← made by make_vault.py
├── travel_agent.py              ← updated
└── chat.py
```

### 2.1 Put your SerpApi key in a vault

Create `make_vault.py`:

```python
"""Run once: store your SerpApi key in a vault at Anthropic."""
import json
import os

import anthropic

client = anthropic.Anthropic()

vault = client.beta.vaults.create(display_name="My Travel App secrets")
client.beta.vaults.credentials.create(
    vault_id=vault.id,
    display_name="SerpApi key",
    auth={
        # Anthropic sends this as "Authorization: Bearer <key>" to this MCP server only.
        "type": "static_bearer",
        "mcp_server_url": "https://mcp.serpapi.com/mcp",
        "token": os.environ["SERPAPI_API_KEY"],
    },
)
json.dump({"vault_id": vault.id}, open("vault.json", "w"))
print("saved", vault.id, "to vault.json")
```

Run it once:

```bash
python make_vault.py
```

✅ **You know it worked when** it prints `saved vlt_… to vault.json`.

### 2.2 Connect the MCP server

Update `agents/travel-agent.md` so it looks like this (new lines are marked `# new`, and there are two new prompt lines at the end):

```markdown
---
name: Travel Agent
model: claude-opus-5
mcp_servers:                                   # new
  - type: url                                  # new
    name: serpapi                              # new
    url: https://mcp.serpapi.com/mcp           # new
tools:
  - type: agent_toolset_20260401
  - type: mcp_toolset                          # new
    mcp_server_name: serpapi                   # new
    default_config:                            # new
      permission_policy: {type: always_allow}  # new
---
You are the travel agent inside My Travel App. You help travelers plan and book trips.
Keep every reply to 1-3 short sentences, in plain text. No Markdown.
Give a short reason for each recommendation.
Search real flights before quoting any price. Never guess prices.
Search with mode "complete", so results include google_flights_url.
```

`permission_policy: always_allow` matters: MCP tools ask for approval by default, and a flight search is harmless.

Upload the change:

```bash
ant apply agents/travel-agent.md
```

✅ **You know it worked when** the plan shows `~ update` for your agent, and in `claude-lock.json` your agent's entry now says `"version": "2"`.

### 2.3 Attach the vault to your sessions

In `travel_agent.py`, load the vault ID below the other IDs, and pass it when you create a session:

```python
VAULT_ID = json.load(open("vault.json"))["vault_id"]
```

```python
def start_session():
    session = client.beta.sessions.create(agent=AGENT_ID, environment_id=ENV_ID, vault_ids=[VAULT_ID])
    return session.id
```

### 2.4 Search

Start the chat:

```bash
python chat.py
```

Ask something like *Flights from SFO to Maui on November 23, one way?* (use a date in the next few months).

✅ **You know it worked when** you see `(search…)` and the reply names real flights and prices. Compare them with [Google Flights](https://www.google.com/travel/flights).

---

## Milestone 3: Use my points

**Goal:** give your agent a **skill** that does the points math in its container, then a **custom tool** that reads the traveler's points from *your* app.

At the end of this milestone, your folder looks like this:

```
travel-agent/
├── .env
├── agents/
│   └── travel-agent.md          ← updated
├── environments/
│   └── travel-env.yaml
├── skills/
│   └── points-estimator/        ← new
│       ├── SKILL.md
│       ├── compute_points.py
│       └── cpp.py
├── claude-lock.json
├── make_vault.py
├── vault.json
├── tools.py                     ← new
├── points.json                  ← made by tools.py
├── travel_agent.py              ← updated
└── chat.py
```

### 3.1 Write a skill

A skill is a folder with a `SKILL.md` and any scripts it needs. Create these three files.

> **About the miles numbers:** this skill *estimates* what a flight costs in miles, from how long the flight is and which cabin you pick. Real award prices vary by airline and date, and there's no free API for them, so we leave getting the true miles price from an API as an [extension](#extensions-optional).

`skills/points-estimator/SKILL.md`:

```markdown
---
name: points-estimator
description: Price a flight in miles and decide whether to pay with points or cash. Use whenever the traveler asks about points or miles.
---
To price a flight in miles, run (FLIGHT_HOURS is the flight time, like 5.5):

    python compute_points.py FLIGHT_HOURS CABIN [round]

CABIN is economy, premium, business, or first. These are sample prices, not live; always say so.

Then work out what the points are worth:

    python cpp.py CASH_PRICE MILES

Using points is worth it at 1.3 cents per point or more. Mention the cents per point when you recommend points or cash.
```

`skills/points-estimator/compute_points.py`:

```python
"""Sample award prices from My Travel App's own chart (not real airline prices).
Usage: python compute_points.py FLIGHT_HOURS CABIN [round]"""
import sys

hours, cabin = float(sys.argv[1]), sys.argv[2].lower()
base = 12500 if hours < 3 else 17500 if hours < 6 else 30000 if hours < 10 else 40000
multiplier = {"economy": 1, "premium": 1.6, "business": 2.2, "first": 3}[cabin]
trips = 2 if sys.argv[-1] == "round" else 1
print(f"{round(base * multiplier * trips, -3):,.0f} miles, {cabin} (sample award price, not live)")
```

`skills/points-estimator/cpp.py`:

```python
"""Cents per point for paying with miles. Usage: python cpp.py CASH_PRICE MILES"""
import sys

cash, miles = float(sys.argv[1]), float(sys.argv[2])
cents = cash / miles * 100
verdict = "great" if cents >= 1.5 else "good" if cents >= 1.3 else "poor"
print(f"{cents:.2f} cents per point ({verdict})")
```

Try a script yourself. It should print 35,000 miles:

```bash
python skills/points-estimator/compute_points.py 5.5 economy round
```


### 3.2 Write a custom tool

Create `tools.py`. Custom tools run in **your** app. This one reads points from a file on your computer, which acts as the app's database:

```python
"""My Travel App's custom tools. They run on your computer, not at Anthropic."""
import json
from pathlib import Path

POINTS_FILE = Path("points.json")


def get_points_balance():
    if not POINTS_FILE.exists():  # start with some sample points
        POINTS_FILE.write_text(json.dumps({"United MileagePlus": 45000, "Chase Ultimate Rewards": 60000}))
    points = json.loads(POINTS_FILE.read_text())
    return ", ".join(f"{program}: {amount:,}" for program, amount in points.items())


TOOLS = {"get_points_balance": get_points_balance}
```

> **About the points:** this app pretends you have 45,000 United miles and 60,000 Chase points. They're saved in `points.json` (created the first time the tool runs), so you can edit them. Connecting to your real points balances is an [extension](#extensions-optional).

### 3.3 Tell the agent about both

In `agents/travel-agent.md`, add the custom tool at the end of `tools`, and a `skills` section after it. The end of the settings now looks like this. Claude only sees the tool's name and description; the code stays in your app.

```yaml
  - type: mcp_toolset
    mcp_server_name: serpapi
    default_config:
      permission_policy: {type: always_allow}
  - type: custom                               # new
    name: get_points_balance                   # new
    description: The traveler's airline and hotel points balances.  # new
    input_schema: {type: object}               # new
skills:                                        # new
  - ../skills/points-estimator                 # new
---
```

Upload the agent and the skill together:

```bash
ant apply agents/travel-agent.md skills/points-estimator
```

✅ **You know it worked when** the plan shows `+ create` for the skill and `~ update` for the agent.

### 3.4 Work it out: why does it break?

Start the chat:

```bash
python chat.py
```

Ask *How many points do I have?*

Something goes wrong. Figure out what, and fix it. Clues:

- What did the agent reply? Send a second message. What error do you get?
- Open the session in the Console. What's the last thing the agent did?
- Look at your loop in `run_turn()`. When does it `break`?

<details>
<summary>Hint 1</summary>

When the agent calls a **custom tool**, it pauses and waits for *your app* to run the tool and send back the result. While it waits, the session goes `session.status_idle`, but with `event.stop_reason.type == "requires_action"`.
</details>

<details>
<summary>Hint 2</summary>

Add `from tools import TOOLS` at the top of `travel_agent.py`, and this function, which runs each tool the agent asked for and sends back the results:

```python
def send_tool_results(session_id, calls):
    results = []
    for call in calls:
        output = TOOLS[call.name](**call.input)
        results.append({
            "type": "user.custom_tool_result",
            "custom_tool_use_id": call.id,
            "content": [{"type": "text", "text": output}],
        })
    client.beta.sessions.events.send(session_id=session_id, events=results)
```

Then make your loop collect `agent.custom_tool_use` events. When the session goes idle with `requires_action`, call `send_tool_results(...)` and keep listening instead of stopping.
</details>

<details>
<summary>Show the fixed loop</summary>

```python
def run_turn(session_id, text):
    with client.beta.sessions.events.stream(session_id=session_id) as stream:
        send_message(session_id, text)
        pending = []
        for event in stream:
            if event.type == "agent.message":
                print(f"\nagent › {event.content[0].text}")
            elif event.type in ("agent.tool_use", "agent.mcp_tool_use"):
                print(f"  ({event.name}…)")
            elif event.type == "agent.custom_tool_use":
                print(f"  (your app runs {event.name}…)")
                pending.append(event)
            elif event.type == "session.status_idle":
                if event.stop_reason.type == "requires_action":
                    send_tool_results(session_id, pending)
                    pending = []
                    continue
                break
```
</details>

✅ **You know it worked when**:
- *How many points do I have?* shows `(your app runs get_points_balance…)` and the reply lists your balances, and
- *Should I use points for a flight from SFO to Maui on November 23?* shows `(bash…)` (the skill running in the container), and the reply mentions the cents per point.

🎉 **You've built it:** an agent file, a container, sessions, an event loop, an MCP tool with a vault, a skill, and a custom tool.

---

## Check your understanding

Five questions, about 5 minutes. Answer each one in a sentence or two, in your own words, before you open the example answer.

**1.** When you asked *Should I use points for a flight from SFO to Maui on November 23?*, your agent took these steps:

- searched for flights
- looked up your points balance with `get_points_balance`
- read `SKILL.md`, then ran `compute_points.py` and `cpp.py`

Where did each one run: your computer, the container at Anthropic, or SerpApi's server?

<details>
<summary>Example answer</summary>

- **Searched for flights:** on **SerpApi's server**. Anthropic called it for the agent and added your key from the vault.
- **Looked up your points balance:** on **your computer**. Your app ran `get_points_balance` in `tools.py`.
- **Read `SKILL.md` and ran the scripts:** in **the container** at Anthropic. These are the `(read…)` and `(bash…)` lines.
</details>

**2.** `compute_points.py` and `get_points_balance` are both code the agent uses. Why is one part of a skill and the other a custom tool?

<details>
<summary>Example answer</summary>

`compute_points.py` is plain math that needs nothing from your app, so it can run in the container. `get_points_balance` needs data only your app has (`points.json` on your computer), and the container can't see your computer. Rule of thumb: if the code needs your app's data, or needs a person, make it a custom tool.
</details>

**3.** Your SerpApi key is in a vault. Say you had pasted it into the system prompt instead. What could go wrong?

<details>
<summary>Example answer</summary>

Claude would see the key, so it could repeat it in a reply or use it in a command. It would also be stored in your agent's settings, where anyone who can see the agent file or your workspace can read it. With a vault, Anthropic adds the key only when it calls SerpApi, so it never enters the conversation or the container.
</details>

**4.** In 3.4, your first loop broke. In your own words: what was the agent waiting for, and why did your next message cause an error?

<details>
<summary>Example answer</summary>

The agent asked your app to run `get_points_balance`, then paused (`session.status_idle` with `requires_action`) until your app sent back a `user.custom_tool_result`. The old loop stopped at any idle, so it never sent one. Your next message failed because the session was still waiting for that result.
</details>

**5.** A teammate wants the agent to tell travelers the weather at their destination. Would you use an MCP server, a skill, a custom tool, or none of these? Why?

<details>
<summary>Example answer</summary>

There's more than one good answer; the reasoning is what matters. Often you need **nothing new**: the built-in toolset already includes web search. If you want reliable, structured forecasts, connect a weather **MCP server**, with its key in the vault. A **custom tool** makes sense only if the weather comes from your own app. A **skill** makes sense if the agent needs know-how, like how to turn a forecast into packing advice.
</details>

---

## Extensions (optional)

Each one is independent, so pick whatever interests you.

| Extension | What you'll build | Needs |
|---|---|---|
| [Ask before booking](#extension-ask-before-booking) | A custom tool that waits for the traveler to say yes | Nothing new |
| [Hotels](#extension-hotels) | Hotel search, from the same SerpApi server | Nothing new |
| [Round trips](#extension-round-trips) | Outbound flights first, then matching return flights | Nothing new |
| [Your own web app](#extension-your-own-web-app) | A web page for your travel agent, instead of the terminal | Nothing new |
| [Remember trips](#extension-remember-trips) | Trips that are still there in your next chat (a memory store) | Nothing new |
| [Price alerts](#extension-price-alerts) | A daily price check that runs on its own (a scheduled deployment) | "Remember trips" |
| [Real points balances](#extension-real-points-balances) | Your real balances, instead of the sample points | Depends on your app |
| [Real miles prices](#extension-real-miles-prices) | Real award prices, instead of the skill's estimate | seats.aero Pro (about $10/month) |

### Extension: Ask before booking

A second custom tool, with one twist: it stops and waits for a person. Add this function to `tools.py`, put `import webbrowser` at the top, and update `TOOLS`:

```python
def book_flight(flight, price, link):
    """Show the traveler where to book, then wait for them to decide."""
    print(f"\n  Book {flight} for {price}?")
    if input("  Open it on Google Flights to book? [y/n] ").strip().lower() != "y":
        return "The traveler said no. Nothing was booked."
    webbrowser.open(link)
    if input("  Did you finish booking? [y/n] ").strip().lower() != "y":
        return "The traveler looked at it but didn't book."
    return f"The traveler booked {flight} for {price}."


TOOLS = {"get_points_balance": get_points_balance, "book_flight": book_flight}
```

Add it at the end of `tools` in `agents/travel-agent.md` (above `skills:`):

```yaml
  - type: custom
    name: book_flight
    description: "Offer to book a flight. The app shows the traveler the flight on Google Flights and asks them to confirm."
    input_schema:
      type: object
      properties:
        flight: {type: string, description: "e.g. 'UA 1957, SFO to OGG, Nov 23'"}
        price: {type: string, description: "e.g. '$571'"}
        link: {type: string, description: "google_flights_url from the search"}
      required: [flight, price, link]
```

Add one line to the prompt:

```
When the traveler wants to book, use book_flight. Never ask for card numbers in chat.
```

Upload the change:

```bash
ant apply agents/travel-agent.md
```

Start the chat, ask for flights, pick one, and say *Book it.*

✅ **You know it worked when** your terminal asks `Open it on Google Flights to book? [y/n]`, `y` opens the flight in your browser (don't actually buy it), and answering `n` to `Did you finish booking?` makes the agent say nothing was booked.

**Why it works this way:** `book_flight` is a custom tool, so it runs in your app, and your app can stop and wait for a person. The agent never sees payment details.

### Extension: Hotels

Add this line to your prompt, then run `ant apply agents/travel-agent.md`:

```
For hotels, search with the google_hotels engine, with the check-in date, check-out date, and number of adults.
```

✅ **You know it worked when** *Find me a hotel in Kaanapali, Nov 23 to Dec 6, for two* shows `(search…)` and the reply names real hotels with nightly prices.

### Extension: Round trips

Add this line to your prompt, then run `ant apply agents/travel-agent.md`:

```
For round trips, show outbound flights first. After the traveler picks one, search again with its departure_token to get the return flights.
```

✅ **You know it worked when** a round-trip request shows outbound options, and after you pick one, the agent searches again and shows return flights.

### Extension: Your own web app

Build a web page where travelers chat with your agent. There are no starter files: how you build it is up to you, and any web framework works.

- Your web server calls the same `start_session()` and `run_turn()` you already wrote.
- The main change: `run_turn()` currently `print`s replies to the terminal. Change it to hand each reply to your web page instead, for example by passing it a function to call for each message.
- Custom tools that use `input()` (like `book_flight`) need a web version too, such as Yes/No buttons.

✅ **You know it worked when** you can chat with your agent in the browser, and its sessions still show up on the [Sessions page](https://platform.claude.com/workspaces/default/sessions).

### Extension: Remember trips

A **memory store** is a set of files that stays around between sessions. The agent reads and writes it like any other files.

1. Create `memory_stores/trips.yaml`:

```yaml
name: trips
description: The traveler's booked trips, one file per trip.
```

2. Upload it:

```bash
ant apply memory_stores/trips.yaml
```

3. In `travel_agent.py`, load its ID from `claude-lock.json` and attach it to every session:

```python
TRIPS_ID = lock["./memory_stores/trips.yaml"]["id"]
```

```python
def start_session():
    session = client.beta.sessions.create(
        agent=AGENT_ID, environment_id=ENV_ID, vault_ids=[VAULT_ID],
        resources=[{"type": "memory_store", "memory_store_id": TRIPS_ID}],
    )
    return session.id
```

4. Add this line to your prompt, then run `ant apply agents/travel-agent.md`:

```
Save each trip the traveler books to the trips memory. At the start of a chat, check it for their trips.
```

✅ **You know it worked when** you tell the agent about a trip you booked, quit, start `chat.py` again, and *What trips do I have?* gets the right answer.

### Extension: Price alerts

A **scheduled deployment** starts a new session on a timer, even when nobody is using your app. You need "Remember trips" first.

1. Create `agents/price-watcher.md` with a new `name` (like `Price Watcher`). Copy your travel agent's `model`, `mcp_servers`, and its `agent_toolset_20260401` and `mcp_toolset` tools (it needs the built-in tools to read the memory files). Give it **no custom tools**: nobody is watching it, so it must never book anything. Its prompt:

```
You check flight prices for trips in the trips memory. For each trip, search today's price.
If it is cheaper than the price on file, write a short note to /proposals/ in the trips memory.
If nothing is cheaper, change nothing.
```

2. Create `deployments/price-check.md`. Paste in your real IDs: `ant apply` doesn't fill in IDs inside `vault_ids` or `resources`.

```markdown
---
name: Daily price check
agent: ../agents/price-watcher.md
environment_id: ../environments/travel-env.yaml
vault_ids: [vlt_...]                  # from vault.json
resources:
  - type: memory_store
    memory_store_id: memstore_...     # from claude-lock.json
schedule: {type: cron, expression: "0 8 * * *", timezone: America/Los_Angeles}
---
Check today's prices for every trip in memory.
```

3. Upload both:

```bash
ant apply agents/price-watcher.md deployments/price-check.md
```

4. Don't wait until 8 a.m.: run it once now. Put the deployment's ID (from `claude-lock.json`) in `DEPLOYMENT_ID`:

```python
import anthropic
anthropic.Anthropic().beta.deployments.run("DEPLOYMENT_ID")
```

It now runs every morning and uses API credits each time. To stop it, run `anthropic.Anthropic().beta.deployments.pause("DEPLOYMENT_ID")`. See [scheduled deployments](https://platform.claude.com/docs/en/managed-agents/scheduled-deployments) in the docs for more.

✅ **You know it worked when** a new session appears on the [Sessions page](https://platform.claude.com/workspaces/default/sessions) and, if a price dropped, a note shows up in `/proposals/`.

### Extension: Real points balances

Airlines and banks don't offer free public APIs for points balances. Two ideas: let travelers type their balances into your app (and save them to `points.json`), or use a paid account-aggregation service. Either way, only `get_points_balance()` in `tools.py` changes; the agent file stays the same.

### Extension: Real miles prices

The skill's miles prices are estimates. For real award prices, subscribe to [seats.aero](https://seats.aero) Pro, then write a custom tool in `tools.py` that calls the [seats.aero API](https://developers.seats.aero/reference/getting-started-p) (it expects your key in a `Partner-Authorization` header). Update `SKILL.md` to use the real price instead of `compute_points.py`.

---

## If something goes wrong

| You see | It means | Fix |
|---|---|---|
| `ant: command not found` | `ant` isn't installed, or your terminal can't find it | Redo [step B](#b-install-ant-anthropics-command-line-tool), then open a new terminal |
| `KeyError: 'SERPAPI_API_KEY'` or an authentication error | Your keys aren't loaded in this terminal | Run `source .venv/bin/activate && set -a && source .env && set +a` |
| `FileNotFoundError: … claude-lock.json` or `vault.json` | You're in the wrong folder, or skipped a step | `cd` into `travel-agent`, then redo 1.3 or 2.1 |
| `mapping value is not allowed in this context` | A YAML line has `: ` inside text | Put that text in quotes |
| `409` when uploading the environment | That environment name is taken | Use a unique name, e.g. `travel-env-yourname` |
| `400 … waiting on responses to events` | The agent is waiting for a custom tool's result | See [3.4](#34-work-it-out-why-does-it-break) |
| Nothing happens for over a minute | A stalled request | Ctrl-C and run it again |
| Your change to the agent doesn't show up | A running chat keeps the agent version it started with | Quit `chat.py` and start it again |

**See what your agent did:** every chat creates a session. Open it on the [Sessions page in the Console](https://platform.claude.com/workspaces/default/sessions) to see each message, tool call, and result, in order.
