# SELPH — References & Source Code Guide

> Created: 2026-04-24
> Purpose: Map every SELPH component to existing source code, templates, and references

---

## How to Use This Document

Every SELPH component maps to:
1. An existing template from this project (`../AISystemDesign/00_Master_Template/`)
2. Open-source reference implementations
3. Official API documentation and SDKs

Build SELPH by filling in the templates — don't start from scratch.

---

## Internal References (This Project)

### 1. Agent Design → `../AISystemDesign/00_Master_Template/05_Agent_Design.md`

SELPH's Twin Engine follows the **Hybrid Agent** pattern from this template:
- **Reactive** for incoming messages (respond fast)
- **Deliberative** for complex tasks (plan before acting)

Key patterns to apply directly:

```
Memory Architecture (already designed in template):
├── Sensory  → raw incoming message (per request)
├── Short-term → current conversation context (Redis)
├── Long-term → user identity profile (PostgreSQL + pgvector)
├── Episodic → past approval/rejection history (PostgreSQL)
└── Semantic → user's content corpus (pgvector embeddings on Railway PostgreSQL)

Agent Loop (from template):
Receive Task → Load Context → Plan → Execute → Autonomy Check → Update Memory

Tool Safety Levels (from template):
├── Read-only  → fetch messages, retrieve profile
├── Write      → update identity profile, store draft
├── Destructive → send message, post reply ← REQUIRES HUMAN APPROVAL
└── External   → Instagram API, Gmail API, ElevenLabs, HeyGen
```

**Action:** Copy `05_Agent_Design.md` → `SELPH/design/05_Agent_Design.md` and fill in SELPH-specific values.

---

### 2. Autonomy Control → `../AISystemDesign/00_Master_Template/07_Autonomy_Control.md`

SELPH's Human-in-the-Loop framework maps directly:

```
3-Mode Model applied to SELPH:
├── Fully Autonomous  → profile updates, confidence scoring, message intake
├── Human-in-the-Loop → draft approval (ALL outbound messages)
└── Human-on-the-Loop → audit log review, weekly calibration

Confidence Thresholds (from template, applied to SELPH):
├── Score >= 0.85  → "Ready to send" — user sees green indicator
├── Score 0.65-0.84 → "Review suggested" — user sees yellow indicator
└── Score < 0.65   → "Needs your input" — user sees red, must edit

Human Actions Available (directly maps to SELPH approval screen):
├── Approve → twin sends message as-is
├── Edit    → user modifies draft, twin learns from diff
├── Reject  → user states reason, twin learns
└── Stop    → emergency pause, all twin activity halts

Audit Log JSON (from template — use exactly this schema):
{
  "task_id": "uuid",
  "step": 1,
  "timestamp": "ISO-8601",
  "agent_action": "send_instagram_dm",
  "confidence": 0.87,
  "escalated": false,
  "human_reviewer": "user_id",
  "human_action": "approve",
  "human_edit": null,
  "final_action": "send_instagram_dm",
  "outcome": "success"
}
```

**Action:** Copy `07_Autonomy_Control.md` → `SELPH/design/07_Autonomy_Control.md` and fill in SELPH-specific thresholds.

---

### 3. Full System Design Template Set
Apply all 15 template files to SELPH:

| Template File | SELPH Application |
|---|---|
| `01_Problem_Statement.md` | Why SELPH exists — the identity problem |
| `02_Requirements.md` | Functional + non-functional requirements |
| `03_Capacity_Estimation.md` | 100K twins, 10M messages/day |
| `04_High_Level_Architecture.md` | Full SELPH system diagram |
| `05_Agent_Design.md` | Twin Engine agent design |
| `06_LLM_Layer.md` | Claude API integration, prompt design |
| `07_Autonomy_Control.md` | Human-in-the-loop framework |
| `08_Human_Interface.md` | Mobile approval app design |
| `09_Data_Flow.md` | Message → draft → approval → send flow |
| `10_API_Design.md` | SELPH backend API spec |
| `11_Database_Design.md` | PostgreSQL + pgvector schema |
| `12_Reliability_Safety.md` | SELPH SAFE framework |
| `13_Observability.md` | Twin approval rate, latency, drift metrics |
| `14_Tradeoffs.md` | Privacy vs capability, autonomy vs trust |
| `15_Future_Evolution.md` | Voice → Avatar → Enterprise roadmap |

---

### 4. AgentCore Patterns → `../AgentCore/PRODUCT.md`

AgentCore is the enterprise version of what SELPH does for individuals.
Borrow these proven patterns:

```
From AgentCore → Apply to SELPH:

Async Execution       → Celery workers process messages in background
Sandboxed Environment → Twin runs in isolated context per user
Multi-Step Planning   → Twin plans response approach before drafting
Self-Correction       → Twin retries with adjusted style on low approval rate
Task Memory           → pgvector (on Railway PostgreSQL) stores identity + episodic memory
Session Replay        → Full audit log with every action replayed
Multi-Model Routing   → LiteLLM (user-selectable LLM) for reasoning, Chatterbox for voice, Linly-Talker for avatar
MCP Foundation        → Future: expose SELPH as MCP server for integrations
```

---

### 5. Agentic AI Ideas → `../AISystemDesign/Agentic_AI_Product_Ideas.md`

Relevant product patterns SELPH can learn from:

| Product Idea | Pattern SELPH Borrows |
|---|---|
| **TasteGraph** (#16) | Real-time preference model per user → SELPH identity profile |
| **IdentityGuardian** (#83) | Behavior monitoring, anomaly detection → SELPH anomaly detection |
| **TrustAndSafety AI** (#47) | Platform trust enforcement → SELPH SAFE framework |
| **AdaptiveTutor** (#66) | Adapts per-user over time → SELPH learning loop |
| **ChurnOracle** (#18) | Predicts user disengagement → SELPH twin drift detection |

---

## External References

### 1. LangGraph — Human-in-the-Loop Pattern

**What it is:** Framework for building stateful agentic workflows with built-in human approval gates.

**Why SELPH needs it:** The approval loop (draft → notify → approve/reject → learn) is exactly what LangGraph's `interrupt()` pattern solves.

**Key Pattern:**
```python
from langgraph.types import interrupt, Command

# In the twin engine node:
def draft_and_await_approval(state):
    draft = generate_draft(state["incoming_message"], state["identity_profile"])
    confidence = score_confidence(draft, state["identity_profile"])

    if confidence < 0.85:
        # Pause graph, send to human
        human_decision = interrupt({
            "draft": draft,
            "confidence": confidence,
            "message_from": state["sender"]
        })
        # Resume with human's decision
        return Command(resume=human_decision)

    return {"draft": draft, "status": "ready"}
```

**Source Code:**
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [Human-in-Loop with LangGraph — MarkTechPost 2026](https://www.marktechpost.com/2026/02/16/how-to-build-human-in-the-loop-plan-and-execute-ai-agents-with-explicit-user-approval-using-langgraph-and-streamlit/)
- [LangGraph interrupt() Pattern — BSWEN 2026](https://docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/)
- [Tanujkumar HITL Agent Pattern](https://github.com/Tanujkumar24/LANGRAPH-HUMAN-IN-LOOP-AGENT-PATTERN)

---

### 2. Phantom — Closest Open-Source Reference

**What it is:** AI co-worker with persistent memory, email identity, and self-evolution engine. Built on Claude Agent SDK.

**Why SELPH needs it:** Phantom already solves the persistent identity + memory + email agent problem. Study it deeply before building.

```
Phantom Features SELPH Can Learn From:
├── Every Phantom agent has its own email address
├── Self-evolution: observes feedback → critiques performance → updates config
├── Persistent memory across sessions
├── Secure credential collection
├── MCP server integration
└── Built on Claude Agent SDK (same stack as SELPH)
```

**Source Code:** [ghostwright/phantom — GitHub](https://github.com/ghostwright/phantom)

---

### 3. Chatterbox — Voice Clone (Default, MIT, Free)

**What it is:** High-performance open-source TTS developed by Resemble AI. MIT license — free for commercial use. Best open-source voice model in 2026.

**GitHub:** [resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)

**SELPH Voice Clone Implementation (Default Path):**
```python
# Self-hosted Chatterbox — MIT license, zero API cost

from chatterbox.tts import ChatterboxTTS

model = ChatterboxTTS.from_pretrained(device="cuda")  # or "cpu"

# Step 1: Create voice clone from user recordings
def create_voice_clone_chatterbox(user_id: str, reference_audio_path: str) -> str:
    # Chatterbox clones voice from a reference audio sample
    voice_id = f"selph_{user_id}"
    model.save_voice_reference(reference_audio_path, voice_id=voice_id)
    return voice_id

# Step 2: Generate speech as user
def generate_voice_response(text: str, voice_id: str) -> bytes:
    wav = model.generate(
        text=text,
        audio_prompt_path=get_voice_reference(voice_id),
        exaggeration=0.5,
        cfg_weight=0.5
    )
    return apply_selph_watermark(wav)
```

**Optional Premium Alternative — ElevenLabs (Paid):**
```python
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

client = ElevenLabs(api_key=USER_ELEVENLABS_API_KEY)  # user brings own key

def create_voice_clone_elevenlabs(user_id: str, audio_files: list[str]) -> str:
    voice = client.voices.ivc.create(
        name=f"selph_{user_id}",
        files=audio_files
    )
    return voice.voice_id

def generate_voice_elevenlabs(text: str, voice_id: str) -> bytes:
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(stability=0.7, similarity_boost=0.85)
    )
    return apply_selph_watermark(audio)
```

**References:**
- [Chatterbox GitHub](https://github.com/resemble-ai/chatterbox)
- [ElevenLabs SDK](https://github.com/elevenlabs/elevenlabs-python) *(optional paid)*

---

### 4. Linly-Talker — Avatar Clone (Default, MIT, Free)

**What it is:** Open-source digital avatar conversational system. Combines LLMs + visual models + talking head generation. MIT license — free for commercial use.

**GitHub:** [Kedreamix/Linly-Talker](https://github.com/Kedreamix/Linly-Talker)

**SELPH Avatar Implementation (Default Path):**
```python
# Self-hosted Linly-Talker — MIT license, zero API cost

import requests

LINLY_API_URL = "http://localhost:7860"  # self-hosted

# Step 1: Create avatar from user video
def create_avatar_linly(user_id: str, video_path: str) -> str:
    response = requests.post(
        f"{LINLY_API_URL}/upload_avatar",
        files={"video": open(video_path, "rb")},
        data={"avatar_id": f"selph_{user_id}"}
    )
    return response.json()["avatar_id"]

# Step 2: Generate video response
def generate_avatar_video_linly(
    text: str,
    avatar_id: str,
    voice_audio_path: str  # Chatterbox-generated audio
) -> str:
    response = requests.post(
        f"{LINLY_API_URL}/generate_video",
        json={
            "avatar_id": avatar_id,
            "audio_path": voice_audio_path,
            "text": text,
            "resolution": "1080p"
        }
    )
    return response.json()["video_path"]
```

**Optional Premium Alternative — HeyGen (Paid):**
```python
import requests

# User brings their own HeyGen API key
def generate_avatar_video_heygen(text: str, avatar_id: str, voice_id: str) -> str:
    response = requests.post(
        "https://api.heygen.com/v2/video/generate",
        headers={"X-Api-Key": USER_HEYGEN_API_KEY},
        json={
            "video_inputs": [{
                "character": {"type": "avatar", "avatar_id": avatar_id},
                "voice": {"type": "elevenlabs", "voice_id": voice_id, "input_text": text}
            }],
            "dimension": {"width": 1280, "height": 720}
        }
    )
    return response.json()["data"]["video_id"]
```

**References:**
- [Linly-Talker GitHub](https://github.com/Kedreamix/Linly-Talker)
- [Duix-Avatar GitHub](https://github.com/duixcom/Duix-Avatar) *(alternative open-source avatar)*
- [HeyGen API Docs](https://www.heygen.com/) *(optional paid)*

---

### 5. LiteLLM + Claude API — Multi-Model Twin Engine Brain

**What it is:** LiteLLM is a Python SDK that provides a single OpenAI-compatible interface to 140+ LLM providers. SELPH uses LiteLLM as the model gateway — claude-sonnet-4-6 is the default, but users can switch to any supported model and bring their own API key.

**GitHub:** [BerriAI/litellm](https://github.com/BerriAI/litellm)

**SELPH Twin Engine — Multi-Model Implementation:**
```python
import litellm
from litellm import completion

# LiteLLM routes to the user's chosen model
# User's model preference and API key stored in their profile

def generate_twin_draft(
    identity_profile: dict,
    incoming_message: str,
    sender_context: dict,
    channel: str,
    conversation_history: list,
    user_model: str = "claude-sonnet-4-6",    # user-selectable
    user_api_key: str = None                  # user brings own key (BYOK)
) -> dict:

    system_prompt = build_twin_system_prompt(identity_profile, channel)

    # Set user's API key if provided (BYOK)
    if user_api_key:
        litellm.api_key = user_api_key

    # LiteLLM handles routing to correct provider automatically
    # claude-sonnet-4-6, gpt-5, gemini/gemini-2.0, deepseek/deepseek-chat,
    # ollama/llama3, mistral/mistral-large all work with the same interface
    response = completion(
        model=user_model,
        max_tokens=500,
        messages=[
            {"role": "system", "content": system_prompt},
            *conversation_history[-5:],
            {
                "role": "user",
                "content": f"""
Incoming {channel} message from {sender_context['name']}:
"{incoming_message}"

Draft a response as {identity_profile['name']}.
Return JSON:
{{
  "draft": "the response text",
  "confidence_factors": {{
    "topic_known": 0.0-1.0,
    "length_match": 0.0-1.0,
    "tone_match": 0.0-1.0,
    "no_avoided_topics": 0.0-1.0,
    "sample_similarity": 0.0-1.0
  }},
  "reasoning": "why you wrote this"
}}
"""
            }
        ]
    )

    return parse_twin_response(response)


def build_twin_system_prompt(profile: dict, channel: str) -> str:
    channel_hints = {
        "instagram_dm": "casual, short, emoji-friendly, max 150 words",
        "gmail": "professional, structured, with greeting and sign-off",
        "whatsapp": "conversational, warm, voice-note friendly"
    }

    return f"""
You are the digital twin of {profile['name']}.

Your identity:
- Domain: {profile['domain']}
- Tone: {profile['tone']}
- Avg response length: {profile['avg_response_length']} words
- Emoji usage: {"frequent" if profile['emoji_usage'] > 0.5 else "minimal"}
- Greeting style: {profile['greeting_style']}
- Sign-off style: {profile['sign_off_style']}
- Topics you know: {", ".join(profile['topics_known'])}
- Topics you never discuss: {", ".join(profile['topics_avoided'])}

Channel context: {channel_hints.get(channel, "professional")}

Examples of how {profile['name']} actually responds:
{format_sample_responses(profile['sample_responses'])}

RULES:
1. Respond EXACTLY as {profile['name']} would
2. Never claim to be AI unless directly asked
3. If topic is unknown or avoided → "Let me get back to you on that"
4. Match the energy of the incoming message
5. Never make commitments, promises, or financial statements
6. Return ONLY the JSON format requested
"""

# Supported models via LiteLLM (user-selectable):
SUPPORTED_MODELS = {
    "claude-sonnet-4-6":      "Anthropic — default, best reasoning",
    "claude-opus-4-6":        "Anthropic — most capable",
    "gpt-5":                  "OpenAI — alternative",
    "gemini/gemini-2.0-flash":"Google — fast, cheap",
    "deepseek/deepseek-chat": "DeepSeek — cost-effective",
    "ollama/llama3":          "Local via Ollama — zero API cost",
    "mistral/mistral-large":  "Mistral — EU-hosted option",
}
```

**Documentation:**
- [LiteLLM Docs](https://docs.litellm.ai/)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Claude API Docs](https://docs.anthropic.com)
- [Ollama — Local Models](https://ollama.ai/) *(for zero-cost local option)*

---

### 6. pgvector — Vector Memory for Identity

SELPH uses pgvector (built into Railway PostgreSQL) for all vector similarity search. No external vector service needed — embeddings are co-located with identity data for <5ms queries.

**SELPH Identity Memory Implementation:**
```python
import voyageai
from sqlalchemy import text

vo = voyageai.Client(api_key=VOYAGE_API_KEY)

def embed_text(text: str) -> list[float]:
    result = vo.embed([text], model="voyage-3", input_type="document")
    return result.embeddings[0]

def store_identity_memory(profile_id: str, memory_type: str, content: str):
    vector = embed_text(content)
    db.execute(text("""
        INSERT INTO identity_samples (profile_id, channel, incoming, response, source, embedding)
        VALUES (:profile_id, 'memory', '', :content, :memory_type, :vector)
    """), {"profile_id": profile_id, "content": content, "memory_type": memory_type, "vector": vector})

def retrieve_relevant_memories(profile_id: str, query: str, top_k: int = 5):
    query_vector = embed_text(query)
    results = db.execute(text("""
        SELECT response FROM identity_samples
        WHERE profile_id = :profile_id
        ORDER BY embedding <=> :query_vector
        LIMIT :top_k
    """), {"profile_id": profile_id, "query_vector": query_vector, "top_k": top_k})
    return [r.response for r in results]
```

---

### 7. LangGraph + Claude Agent SDK — Full Agent Orchestration

**The 2026 production pattern:**

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from typing import TypedDict, Annotated

class TwinState(TypedDict):
    user_id: str
    incoming_message: str
    sender: dict
    channel: str
    identity_profile: dict
    draft: str
    confidence: float
    human_decision: str
    final_message: str
    audit_log: list

# All node functions MUST be defined BEFORE graph construction to avoid NameError

def load_identity_node(state: TwinState): ...      # implement in Phase 1
def generate_draft_node(state: TwinState): ...     # implement in Phase 2
def score_confidence_node(state: TwinState): ...   # implement in Phase 2
def send_message_node(state: TwinState): ...       # implement in Phase 5
def update_memory_node(state: TwinState): ...      # implement in Phase 1

def await_human_approval_node(state: TwinState):
    # Uses LangGraph interrupt() to pause graph and wait for human decision
    decision = interrupt({
        "draft": state["draft"],
        "confidence": state["confidence"],
        "sender": state["sender"],
        "channel": state["channel"]
    })
    return {"human_decision": decision["action"], "final_message": decision["content"]}

# Build the Twin Engine graph AFTER all node functions are defined
graph = StateGraph(TwinState)

graph.add_node("load_identity", load_identity_node)
graph.add_node("generate_draft", generate_draft_node)
graph.add_node("score_confidence", score_confidence_node)
graph.add_node("await_human_approval", await_human_approval_node)
graph.add_node("send_message", send_message_node)
graph.add_node("update_memory", update_memory_node)

graph.add_edge(START, "load_identity")
graph.add_edge("load_identity", "generate_draft")
graph.add_edge("generate_draft", "score_confidence")
graph.add_edge("score_confidence", "await_human_approval")  # Always await human

graph.add_conditional_edges(
    "await_human_approval",
    lambda s: s["human_decision"],
    {
        "approve": "send_message",
        "edit": "send_message",    # edited content in final_message
        "reject": "update_memory", # skip send, just learn
        "skip": END
    }
)

graph.add_edge("send_message", "update_memory")
graph.add_edge("update_memory", END)

# Compile with checkpointing (required for interrupt())
checkpointer = MemorySaver()
twin_engine = graph.compile(checkpointer=checkpointer)
```

**References:**
- [LangGraph + Claude SDK Guide 2026](https://www.mager.co/blog/2026-03-07-langgraph-claude-agent-sdk-ultimate-guide/)
- [LangGraph Docs](https://www.langchain.com/langgraph)
- [Production HITL Pattern 2026](https://growwstacks.com/blog/human-in-the-loop-ai-agents-langgraph)

---

## Project Directory Structure

```
SELPH/
└── docs/
    ├── PRODUCT_IDEA.md          ✅ Vision
    ├── VALIDATION.md            ✅ Market research
    ├── RISK_MITIGATION.md       ✅ Risk framework
    ├── PRD.md                   ✅ Product requirements
    ├── MVP_BUILD_PLAN.md        ✅ Build phases
    └── REFERENCES.md            ✅ This file

SELPH/design/                ← Fill in from Master Template
│   ├── 01_Problem_Statement.md
│   ├── 02_Requirements.md
│   ├── 03_Capacity_Estimation.md
│   ├── 04_High_Level_Architecture.md
│   ├── 05_Agent_Design.md   ← From ../AISystemDesign/00_Master_Template/
│   ├── 06_LLM_Layer.md
│   ├── 07_Autonomy_Control.md ← From ../AISystemDesign/00_Master_Template/
│   ├── 08_Human_Interface.md
│   ├── 09_Data_Flow.md
│   ├── 10_API_Design.md
│   ├── 11_Database_Design.md
│   ├── 12_Reliability_Safety.md
│   ├── 13_Observability.md
│   ├── 14_Tradeoffs.md
│   └── 15_Future_Evolution.md
│
└── src/                     ← Code starts here (Phase 0)
    ├── backend/             FastAPI
    ├── mobile/              React Native
    └── worker/              Celery
```

---

## Build Order with References

| Phase | What to Build | Reference |
|---|---|---|
| 0 | Foundation | FastAPI docs, Supabase Auth |
| 1 | Identity Core | pgvector (Railway PostgreSQL), Voyage AI embeddings |
| 2 | Twin Engine | LiteLLM (multi-model), LangGraph StateGraph |
| 2a | Model Selector | LiteLLM router, user BYOK settings UI |
| 3 | Approval Loop | LangGraph interrupt(), Firebase FCM |
| 4 | Channel Connect | Instagram Graph API, Gmail API |
| 5 | Safety Layer | C2PA watermarking, content moderation APIs |
| 6 | Voice Clone | Chatterbox (default, free) / ElevenLabs (optional) |
| 7 | Avatar Clone | Linly-Talker (default, free) / HeyGen (optional) |
| 8 | Beta Launch | Monitoring, analytics, feedback loops |

---

## Key Open Source Projects to Study

| Project | URL | License | What to Learn |
|---|---|---|---|
| **Phantom** | [github.com/ghostwright/phantom](https://github.com/ghostwright/phantom) | MIT | Persistent identity + memory + email agent |
| **LangGraph HITL** | [github.com/Tanujkumar24/LANGRAPH-HUMAN-IN-LOOP-AGENT-PATTERN](https://github.com/Tanujkumar24/LANGRAPH-HUMAN-IN-LOOP-AGENT-PATTERN) | MIT | Human approval gate pattern |
| **LiteLLM** | [github.com/BerriAI/litellm](https://github.com/BerriAI/litellm) | MIT | Multi-model LLM gateway, BYOK, cost tracking |
| **Chatterbox** | [github.com/resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) | MIT | Voice cloning — free default |
| **Linly-Talker** | [github.com/Kedreamix/Linly-Talker](https://github.com/Kedreamix/Linly-Talker) | MIT | Talking avatar — free default |
| **Duix-Avatar** | [github.com/duixcom/Duix-Avatar](https://github.com/duixcom/Duix-Avatar) | MIT | Alternative open-source avatar |
| **Ollama** | [github.com/ollama/ollama](https://github.com/ollama/ollama) | MIT | Run LLMs locally at zero cost |
| **AI Avatar System** | [github.com/PunithVT/ai-avatar-system](https://github.com/PunithVT/ai-avatar-system) | MIT | Photo + voice clone + lip-sync (Claude + Whisper + MuseTalk) |
| **Claude Code** | [github.com/yasasbanukaofficial/claude-code](https://github.com/yasasbanukaofficial/claude-code) | MIT | LLM tool-calling, agentic workflows |
| **Ruflo** | [github.com/ruvnet/ruflo](https://github.com/ruvnet/ruflo) | MIT | Multi-agent swarm orchestration |

---

*Status: References compiled — Ready to scaffold source code*
