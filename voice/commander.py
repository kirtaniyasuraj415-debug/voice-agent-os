"""Voice Commander - the assistant that controls the whole OS by voice.

"Baaton-baaton mein system control": spoken commands are mapped to
concrete OS actions (agents, calls, clients, status). Unknown requests
fall through to the NVIDIA LLM which knows the command grammar.
"""
from __future__ import annotations

import logging
import re

from agents.base import BaseAgent
from agents.manager import agent_manager
from calling.manager import call_manager
from core.config import settings
from core.registry import registry
from marketplace.tenant_manager import tenant_manager
from nvidia.base import ChatMessage

log = logging.getLogger("vaos.voice.commander")

COMMAND_HELP = """
Available voice commands:
- "create agent named X"                -> new voice agent
- "call <number> with agent <name>"     -> start a phone call
- "list agents" / "agent status"        -> show agents
- "team" / "ask researcher"             -> summon the built-in team
- "clients" / "report for client X"     -> marketplace usage
- "system status" / "how are you"       -> OS health
- "help"                                 -> this list
"""


class VoiceCommander(BaseAgent):
    kind = "commander"

    def __init__(self) -> None:
        super().__init__("cmd_nova", settings.assistant_name)
        self.auto_grant = settings.assistant_auto_grant
        self.last_action: str | None = None

    # ------------------------------------------------------------ intents
    def respond(self, user_text: str) -> str:
        text = user_text.strip().lower().rstrip("?.!")
        if not text:
            return "Say something like: create agent named sales."
        if self._matches(text, "help", "what can you do", "commands"):
            return COMMAND_HELP
        if self._matches(text, "status", "how are you", "health", "how is the system"):
            return self.action_status()
        if self._matches(text, "list agent", "show agent", "agent status"):
            return self.action_list_agents()
        if self._matches(text, "create agent", "make agent", "new agent", "add agent"):
            return self.action_create_agent(user_text)
        if self._matches(text, "call", "dial", "phone", "ring"):
            return self.action_call(user_text)
        if self._matches(text, "team", "researcher", "summarizer", "support agent"):
            return self.action_team(user_text)
        if self._matches(text, "client", "report", "usage", "subscription", "bill"):
            return self.action_client_report(user_text)
        return self.action_fallback(user_text)

    # ------------------------------------------------------------ actions
    def action_status(self) -> str:
        running = registry.running_count()
        agents = len(agent_manager.list_agents())
        clients = len(tenant_manager.list_clients())
        calls = call_manager.engine.active_calls()
        from nvidia.factory import nvidia_stack

        return (
            f"System status: {running} agents running, {agents} voice agents configured, "
            f"{clients} clients, {calls} active calls. Providers: {nvidia_stack.describe()}."
        )

    def action_list_agents(self) -> str:
        agents = agent_manager.list_agents()
        if not agents:
            return "No voice agents yet. Say: create agent named sales."
        names = ", ".join(f"{a.name} ({a.id}, {a.status.value})" for a in agents[:10])
        return f"You have {len(agents)} voice agents: {names}."

    def action_create_agent(self, raw: str) -> str:
        m = re.search(r"named\s+([\w\- ]+?)(?:\s+with|\s+for|\s*$)", raw.lower())
        name = (m.group(1).strip() if m else None) or "Untitled agent"
        record = agent_manager.create_agent(name=name.capitalize())
        agent_manager.start_voice_agent(record.id)
        self.last_action = f"create_agent:{record.id}"
        return f"Voice agent '{record.name}' created and started. It is ready to take calls."

    def action_call(self, raw: str) -> str:
        number_match = re.search(r"(\+?\d[\d\s\-]{7,})", raw)
        if not number_match:
            return "Please say a phone number, like: call plus one five five five zero one zero zero with agent sales."
        number = re.sub(r"\s+", "", number_match.group(1))
        agent = None
        name_match = re.search(r"(?:agent|with)\s+([\w\- ]+)$", raw.lower())
        if name_match:
            agent = self._find_agent_by_name(name_match.group(1).strip())
        if agent is None:
            agent = agent_manager.get_agent("ag_sales")
        if agent is None:
            return "I could not find a matching voice agent. Say: create agent named sales, then call the number again."
        call = call_manager.place(agent.id, number)
        self.last_action = f"call:{call.id}"
        return (
            f"Call placed to {number} using agent '{agent.name}'. "
            f"Status: {call.status.value}. It is now talking to the caller."
        )

    def action_team(self, raw: str) -> str:
        if "researcher" in raw:
            agent = agent_manager.get_team_agent("researcher")
        elif "summarizer" in raw:
            agent = agent_manager.get_team_agent("summarizer")
        elif "support" in raw:
            agent = agent_manager.get_team_agent("support")
        else:
            team = agent_manager.team_status()
            return "System team is online: " + ", ".join(f"{k}={'up' if v else 'down'}" for k, v in team.items())
        if agent is None:
            return "That team member is not running."
        question = raw.split(agent.name.lower(), 1)[-1].strip() or "give a status summary"
        reply = agent.respond(question)
        self.last_action = f"team:{agent.agent_id}"
        return f"{agent.name} says: {reply}"

    def action_client_report(self, raw: str) -> str:
        clients = tenant_manager.list_clients()
        if not clients:
            return "No clients yet. Say: add client Acme with pro plan."
        client = clients[0]
        name_match = re.search(r"(?:for|client)\s+([\w\- ]+)$", raw.lower())
        if name_match:
            for c in clients:
                if name_match.group(1).lower() in c.name.lower():
                    client = c
                    break
        report = tenant_manager.usage_report(client.id)
        return (
            f"Client {report['client']} on {report['plan']} plan: {report['minutes_used']} minutes "
            f"used of {report['monthly_limit_minutes']}, {report['subscribed_agents']} agents subscribed, "
            f"estimated bill {report['estimated_bill']} dollars."
        )

    def action_fallback(self, text: str) -> str:
        """Let the LLM interpret the request using the command grammar."""
        prompt = (
            "You are the voice commander of a voice-agent operating system. "
            f"The user said: {text!r}. If this looks like an OS command (create agent, "
            "make a call, client report, system status), reply with the closest command name "
            "from: create_agent, call, status, clients, team. Otherwise reply naturally and briefly."
        )
        reply = self.llm.chat([ChatMessage("user", prompt)])
        return f"[commander] {reply}"

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _matches(text: str, *keys: str) -> bool:
        return any(k in text for k in keys)

    def _find_agent_by_name(self, name: str):
        for agent in agent_manager.list_agents():
            if agent.name.lower() == name or name in agent.name.lower():
                return agent
        return None

    def describe(self) -> dict:
        data = super().describe()
        data["auto_grant"] = self.auto_grant
        return data


commander = VoiceCommander()
