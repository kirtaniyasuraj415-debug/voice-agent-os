"""Interactive operator console - manage the OS from the terminal."""
from __future__ import annotations

import shlex

from agents.manager import agent_manager
from calling.manager import call_manager
from core.registry import registry
from marketplace.tenant_manager import tenant_manager
from nvidia.factory import nvidia_stack
from voice.commander import commander

BANNER = r"""
   __     ___   _____     __        __    __          ___   ____
  |  |   /   \  \   _\    |  |      |  |  |  |        /  _] |    \
  |  |  |     |  |  |     |  |   ___|  |  |  |___    /  [_  |  D  )
  |  |  |  O  |  |  |     |  |  |___|  |  |   _  \  |    _] |    /
  |  |  |     |  |  |     |  |       |  |  |  |  |  |   [_  |    \
  |  |  |     |  |  |  ___|  |       |  |  |  |  |  |     | |  .  \
  |__|  \___/  |__|  |_____|       |__|  |__|  |__| |_____| |__|\_|
   Voice Agent OS - command the system by voice or text
"""


def cmd_help() -> str:
    return "\n".join(
        [
            "Commands:",
            "  status                          OS health + providers",
            "  agents                          list voice agents",
            "  agent create <name>             new voice agent",
            "  agent start <id> / stop <id>",
            "  call <agent_id> <phone>         place a call",
            "  calls                           recent calls",
            "  team                            system team status",
            "  ask <agent_id> <text>           ask a voice agent something",
            "  clients / client add <name> <plan>",
            "  report <client_id>              usage + bill",
            "  nova <command...>               say it to the commander",
            "  help / exit",
        ]
    )


def handle(line: str) -> str:
    args = shlex.split(line)
    if not args:
        return ""
    verb = args[0].lower()

    if verb in ("help", "?"):
        return cmd_help()
    if verb == "exit":
        return "__EXIT__"
    if verb in ("status", "os"):
        return commander.action_status()
    if verb == "agents":
        return commander.action_list_agents()
    if verb == "agent":
        sub = args[1] if len(args) > 1 else "help"
        if sub == "create":
            record = agent_manager.create_agent(name=" ".join(args[2:]) or "Untitled")
            agent_manager.start_voice_agent(record.id)
            return f"created + started {record.id} ({record.name})"
        if sub in ("start", "stop"):
            agent_id = args[2] if len(args) > 2 else ""
            if sub == "start":
                runtime = agent_manager.start_voice_agent(agent_id)
                return f"started {agent_id}" if runtime else f"agent {agent_id} not found/inactive"
            return "stopped" if agent_manager.stop_voice_agent(agent_id) else "not running"
    if verb == "call":
        if len(args) < 3:
            return "usage: call <agent_id> <phone>"
        call = call_manager.place(args[1], args[2])
        return f"call {call.id} -> {call.to_number}: {call.status.value}"
    if verb == "calls":
        return "\n".join(f"{c.id} {c.status.value} {c.to_number} ({c.duration_seconds}s)" for c in call_manager.list(limit=10))
    if verb == "team":
        return "team: " + ", ".join(f"{k}={'up' if v else 'down'}" for k, v in agent_manager.team_status().items())
    if verb == "ask":
        if len(args) < 3:
            return "usage: ask <agent_id> <text...>"
        runtime = agent_manager.get_runtime(args[1])
        return runtime.respond(" ".join(args[2:])) if runtime else "agent not found"
    if verb == "clients":
        clients = tenant_manager.list_clients()
        if not clients:
            return "no clients yet"
        return "\n".join(f"{c.id} {c.name} ({c.plan}) key={c.api_key[:8]}..." for c in clients)
    if verb == "client":
        if args[1] == "add":
            name = " ".join(args[2:-1]) or "Unnamed"
            plan = args[-1] if args[-1] in ("starter", "pro", "enterprise") else "starter"
            client = tenant_manager.create_client(name=name, email="client@example.com", plan=plan)
            return f"created client {client.id} api_key={client.api_key}"
    if verb == "report":
        if len(args) < 2:
            return "usage: report <client_id>"
        return str(tenant_manager.usage_report(args[1]))
    if verb == "nova":
        return commander.respond(" ".join(args[1:]))
    return f"unknown command: {verb} (try 'help')"


def run_console() -> None:
    print(BANNER)
    print(nvidia_stack.describe())
    print("Type 'help' for commands, 'exit' to quit.\n")
    while True:
        try:
            line = input("vaos> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break
        if not line:
            continue
        out = handle(line)
        if out == "__EXIT__":
            print("bye")
            break
        print(out)
