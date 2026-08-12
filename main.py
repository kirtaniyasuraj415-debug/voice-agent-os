"""Voice Agent OS - entry point.

Commands:
    python main.py serve      -> REST API + team + scheduler
    python main.py console    -> interactive operator console
    python main.py voice      -> live voice pipeline (mic/simulated)
    python main.py demo       -> end-to-end scripted demo
"""
from __future__ import annotations

import argparse
import logging
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="vaos", description="Voice Agent OS")
    parser.add_argument("command", nargs="?", default="serve", help="serve | console | voice | demo")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    if args.command == "serve":
        _serve()
    elif args.command == "console":
        from agents.manager import agent_manager

        agent_manager.boot_team()
        from cli.console import run_console

        run_console()
    elif args.command == "voice":
        from agents.manager import agent_manager
        from voice.pipeline import pipeline

        agent_manager.boot_team()
        pipeline.run_interactive()
    elif args.command == "demo":
        _demo()
    else:
        parser.print_help()
        sys.exit(1)


def _serve() -> None:
    import uvicorn

    from core.config import settings

    uvicorn.run("api.server:app", host=settings.api_host, port=settings.api_port)


def _demo() -> None:
    """Full end-to-end demo without any external service."""
    from agents.manager import agent_manager
    from calling.manager import call_manager
    from marketplace.tenant_manager import tenant_manager
    from voice.commander import commander

    agent_manager.boot_team()
    print("== Voice Agent OS demo ==")

    print("\n1) Speak to the commander (voice command -> OS action)")
    for text in [
        "how are you",
        "create agent named sales",
        "list agents",
    ]:
        reply = commander.respond(text)
        print(f"   you: {text}\n   nova: {reply}")

    print("\n2) Sell to a client (marketplace)")
    client = tenant_manager.create_client("Acme Corp", "billing@acme.com", plan="pro")
    print(f"   created client {client.name} -> api_key={client.api_key[:12]}...")
    sales = agent_manager.list_agents()[0]
    tenant_manager.subscribe(client.id, sales.id)
    print(f"   subscribed {client.name} to {sales.name}")

    print("\n3) Make a phone call with the voice agent (mock telephony)")
    call = call_manager.place(sales.id, "+15550100", tenant_id=client.id)
    print(f"   call {call.id} -> {call.to_number}: {call.status.value}")
    for turn in call.transcript:
        print(f"   [{turn['speaker']}] {turn['text']}")

    print("\n4) Client usage report")
    print("   ", tenant_manager.usage_report(client.id))

    print("\n5) OS status")
    print("   ", commander.action_status())
    print("\nDemo finished. Try: python main.py serve / console / voice")


if __name__ == "__main__":
    main()
