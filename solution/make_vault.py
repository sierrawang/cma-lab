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
