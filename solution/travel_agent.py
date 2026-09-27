"""Talks to your Travel Agent on Claude Managed Agents."""
import json

import anthropic

from tools import TOOLS

client = anthropic.Anthropic()

# The IDs that `ant apply` saved
lock = json.load(open("claude-lock.json"))["resources"]
AGENT_ID = lock["./agents/travel-agent.md"]["id"]
ENV_ID = lock["./environments/travel-env.yaml"]["id"]
VAULT_ID = json.load(open("vault.json"))["vault_id"]


def start_session():
    session = client.beta.sessions.create(agent=AGENT_ID, environment_id=ENV_ID, vault_ids=[VAULT_ID])
    return session.id


def send_message(session_id, text):
    client.beta.sessions.events.send(
        session_id=session_id,
        events=[{"type": "user.message", "content": [{"type": "text", "text": text}]}],
    )


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
