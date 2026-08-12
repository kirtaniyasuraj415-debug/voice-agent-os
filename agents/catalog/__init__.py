"""Built-in system-team agents, adapted from the 500-AI-Agents-Projects collection.

Each agent is self-contained (prompt + shared NVIDIA LLM) so the whole
"team" can be summoned by the voice commander without external deps.
"""
from agents.catalog.support import SUPPORT_AGENT_DEF, SupportAgent
from agents.catalog.researcher import RESEARCHER_AGENT_DEF, ResearchAgent
from agents.catalog.summarizer import SUMMARIZER_AGENT_DEF, SummarizerAgent

SYSTEM_TEAM = {
    "support": SUPPORT_AGENT_DEF,
    "researcher": RESEARCHER_AGENT_DEF,
    "summarizer": SUMMARIZER_AGENT_DEF,
}

AGENT_CLASSES = {
    "support": SupportAgent,
    "researcher": ResearchAgent,
    "summarizer": SummarizerAgent,
}

TEAM_NAMES = "support, researcher, summarizer"
