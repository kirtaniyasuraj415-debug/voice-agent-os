# Voice Agent OS (VA-OS)

An **agentic operating system for voice calling agents**, built on NVIDIA's AI stack.

- 🎙️ **Voice assistant commander** — control the *entire OS by voice or text* ("create an agent", "call this number", "client report", "system status").
- 🤖 **Multiple voice agents** — create, prompt, start and stop unlimited voice agents.
- 📞 **Calling agents** — every voice agent can make phone calls (simulated, or real PSTN via Twilio).
- 💳 **Sell to clients** — multi-tenant marketplace: clients get API keys, plans, subscriptions and usage-based billing.
- 🧠 **NVIDIA powered** — LLM via NVIDIA NIM / AI Endpoints, ASR + TTS via NVIDIA Riva cloud (with offline mock fallbacks).
- 🧩 **Clean architecture** — every feature lives in its own section (`core`, `nvidia`, `voice`, `agents`, `calling`, `marketplace`, `api`, `cli`).
- 🧪 Fully tested (`pytest`), zero external services needed to run.

---

## 1. Install

```bash
cd ~/projects/voice-agent-os
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # optional: add NVIDIA + Twilio keys
```

> Without any key the OS runs on `mock` providers so you can test everything.

## 2. Run

```bash
# Option A: full end-to-end scripted demo
python main.py demo

# Option B: REST API server  ->  http://localhost:8000/docs
python main.py serve

# Option C: interactive operator console
python main.py console

# Option D: live voice pipeline (needs a mic or keep it simulated)
python main.py voice
```

## 2b. Deploy live on Vercel (free)

The repo ships with `vercel.json` + `api/index.py` and is already live at:

> **https://voice-agent-os.vercel.app**  (FastAPI docs: `/docs`)

```bash
npx vercel deploy --prod \
  --env NVIDIA_API_KEY=your-key \
  --env PROVIDER_LLM=nvidia \
  --env API_ADMIN_KEY=your-admin-key
```

> **Serverless notes:** SQLite lives in ephemeral `/tmp` on Vercel, so data resets
> on cold starts. For a production multitenant service, swap `storage/db.py` for a
> hosted Postgres. Long-running telephony (Twilio media streams) works best on a
> VPS/Render/Railway instead of serverless.

## 3. Try it in 30 seconds

```bash
python main.py demo
```

This shows the five pillars:

1. Speak to **Nova** (the commander) → it creates a voice agent.
2. Create a **client**, they get an API key + plan.
3. Subscribe the client to the agent.
4. Place a **phone call** — mock telephony runs a full scripted conversation and records the transcript.
5. Read the **usage report** — minutes metered and billed.

---

## Architecture (one section per feature)

```
voice-agent-os/
├── main.py                    # entry point (serve / console / voice / demo)
├── .env.example               # all knobs: NVIDIA, Twilio, server
│
├── core/                      # OS KERNEL
│   ├── config.py              # settings from .env
│   ├── events.py              # pub/sub event bus (all sections communicate via events)
│   ├── models.py              # VoiceAgent, Call, Client, Subscription
│   └── registry.py            # live agent registry + health
│
├── nvidia/                    # NVIDIA INTEGRATION LAYER
│   ├── base.py                # LLM / ASR / TTS provider interfaces
│   ├── llm.py                 # NVIDIA NIM/AI Endpoints  (mock fallback)
│   ├── asr.py                 # NVIDIA Riva cloud ASR     (mock fallback)
│   ├── tts.py                 # NVIDIA Riva cloud TTS     (mock fallback)
│   └── factory.py             # provider selection from .env
│
├── voice/                     # VOICE SECTION
│   ├── commander.py           # "Nova" - the voice brain that controls the OS
│   ├── pipeline.py            # record -> ASR -> commander -> TTS -> speak
│   └── audio.py               # microphone/speaker I/O (mock safe)
│
├── agents/                    # AGENTS SECTION
│   ├── base.py                # shared agent contract
│   ├── runtime.py             # runnable voice agent (system prompt + LLM)
│   ├── factory.py             # build agents from stored records
│   ├── manager.py             # create/start/stop/list agents + team
│   └── catalog/               # built-in system team (from 500-AI-Agents-Projects)
│       ├── support.py         # customer support agent
│       ├── researcher.py      # web research agent
│       └── summarizer.py      # news summarizer agent
│
├── calling/                   # CALLING SECTION
│   ├── base.py                # TelephonyProvider interface
│   ├── engine.py              # one-call orchestrator + transcript + metering
│   ├── mock_provider.py       # simulated calls (no phone needed)
│   ├── twilio_provider.py     # real PSTN calls via Twilio
│   ├── manager.py             # call API + TwiML/speech webhooks + TTS
│   └── scheduler.py           # scheduled outbound calls
│
├── marketplace/               # MARKETPLACE SECTION (sell to clients)
│   ├── billing.py             # plan limits & per-minute pricing
│   └── tenant_manager.py      # clients, API keys, subscriptions, usage metering
│
├── api/                       # REST API SECTION (one route module per feature)
│   ├── security.py            # admin key + client API-key auth
│   ├── server.py              # FastAPI app factory
│   └── routes/
│       ├── agents_routes.py   # CRUD + start/stop
│       ├── calls_routes.py    # place/list + Twilio webhooks + TTS audio
│       ├── clients_routes.py  # marketplace
│       ├── system_routes.py   # health/status + voice echo
│       └── voice_routes.py    # assistant command endpoint
│
├── cli/                       # CLI SECTION (operator console)
│   └── console.py
└── storage/                   # PERSISTENCE (SQLite)
    └── db.py
```

---

## 4. How to use it (the "sell to clients" flow)

**As the OS owner (admin):**

```bash
# create a paying client (they get an API key)
curl -X POST localhost:8000/api/v1/clients \
  -H "X-Admin-Key: change-me-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Corp","email":"billing@acme.com","plan":"pro"}'
```

**As the client (their API key):**

```bash
# their agents
curl -X POST localhost:8000/api/v1/agents \
  -H "X-Api-Key: vaos_<client_key>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sales Bot","system_prompt":"You sell shoes."}'

# place a phone call with that agent
curl -X POST localhost:8000/api/v1/calls \
  -H "X-Api-Key: vaos_<client_key>" \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"ag_...","to_number":"+15550100"}'

# usage + estimated bill
curl localhost:8000/api/v1/clients/me -H "X-Api-Key: vaos_<client_key>"
```

## 5. The voice commander ("baaton-baaton mein control")

`voice/commander.py` maps spoken commands to OS actions:

| You say | The OS does |
|---|---|
| "create agent named sales" | creates + starts a voice agent |
| "call +15550100 with agent sales" | places a phone call |
| "list agents" | lists all voice agents |
| "team" / "ask researcher ..." | summons the built-in system team |
| "client report for Acme" | usage + bill report |
| "system status" / "how are you" | OS health + providers |

Unknown requests fall through to the NVIDIA LLM, which knows the command grammar.

## 6. Real NVIDIA + Twilio

```bash
# .env
NVIDIA_API_KEY=...            # from https://org.ngc.nvidia.com/setup/api-key
PROVIDER_LLM=nvidia           # LLM via NVIDIA NIM/AI Endpoints
PROVIDER_ASR=nvidia           # Riva cloud ASR (grpc.nvcf.nvidia.com)
PROVIDER_TTS=nvidia           # Riva cloud TTS
PROVIDER_TELEPHONY=twilio     # real phone calls
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1XXXXXXXXXX
```

**Best LLM models for voice (measured on a real NVIDIA key):**

| Model | Latency | Verdict |
|---|---|---|
| `minimaxai/minimax-m3` | ~0.7s | ✅ **Default - use this for voice agents** |
| `z-ai/glm-5.2` | ~95s | Powerful but too slow for phone calls; use for offline planning |
| `meta/llama-3.3-70b-instruct` | slow cold start | fine for non-realtime work |

> Set `NVIDIA_LLM_MODEL` in `.env` to switch. If NVIDIA rate-limits (429) or is
> down, `ResilientLLM` automatically degrades to the offline mock brain so a call
> never dies mid-conversation. NVIDIA **free keys** allow only a few calls per
> minute — buy paid credits (NGC) before selling to clients.

Real phone calls use the **TwiML `<Gather input="speech">` loop**: the API serves NVIDIA-generated TTS audio (`/api/v1/calls/{id}/twiml` → `/api/v1/tts`) and feeds caller speech back into the agent's LLM (`/api/v1/calls/{id}/turn`). Point Twilio's webhook at your public URL.

## 7. Tests

```bash
pytest tests/ -v      # 13 passing tests covering all sections
```

## 8. Data

Everything persists in SQLite (`data/vaos.db`): agents, calls (+transcripts), clients, subscriptions. Delete the folder to reset the OS.

---

### Notes on the 500-AI-Agents-Projects connection

This OS treats that repo as the **agent catalogue**: the `agents/catalog/` team
(support, researcher, summarizer) is adapted from `13-customer-support-agent`,
`01-web-research-agent` and `06-news-summarizer-agent`, but any of the 500 agents
can be registered the same way — as a self-contained prompt + shared LLM runtime.

---

## 9. Handing it to clients (the selling playbook)

You sell **access**, not code. Each client is a tenant with their own API key:

1. **Create the client** (you, as admin)
   ```bash
   curl -X POST https://voice-agent-os.vercel.app/api/v1/clients \
     -H "X-Admin-Key: change-me-admin-key" -H "Content-Type: application/json" \
     -d '{"name":"Acme Corp","email":"billing@acme.com","plan":"pro"}'
   ```
   Response contains `api_key` (e.g. `vaos_...`). That key is the client's whole
   world — they never see your NVIDIA key, your Twilio key, or your admin key.

2. **Send the client this one-pager** (client works with ONLY their API key):
   ```bash
   # list / create their voice agents
   curl -H "X-Api-Key: vaos_..." https://voice-agent-os.vercel.app/api/v1/agents

   # create a support bot
   curl -X POST https://voice-agent-os.vercel.app/api/v1/agents \
     -H "X-Api-Key: vaos_..." -H "Content-Type: application/json" \
     -d '{"name":"Support Bot","system_prompt":"You answer product questions."}'

   # make it call someone
   curl -X POST https://voice-agent-os.vercel.app/api/v1/calls \
     -H "X-Api-Key: vaos_..." -H "Content-Type: application/json" \
     -d '{"agent_id":"ag_...","to_number":"+15550100"}'

   # check usage + their bill
   curl -H "X-Api-Key: vaos_..." https://voice-agent-os.vercel.app/api/v1/clients/me
   ```

3. **Charge them** — the usage report already returns `estimated_bill`
   (price per minute depends on plan). Invoice monthly.

4. **Scale safety** — each client is rate-limited by their plan
   (`monthly_minutes`, `max_agents` in `marketplace/billing.py`). Bump a plan,
   their limits go up automatically.

5. **White-label** — rename the product (logo, agent names, voice) and sell the
   same OS to unlimited clients. Data is already isolated per tenant.
