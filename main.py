import os
import json
import warnings
from hindsight import HindsightEmbedded
from google import genai

# Suppress minor library warnings for a clean terminal output
warnings.filterwarnings("ignore")

# 1. API Configuration
GEMINI_API_KEY = "paste api key here"
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

# Using the active Google Gemini model recommended by the API
ACTIVE_MODEL = "gemini-3.5-flash-lite"

print("=" * 70)
print(">>> AutoOps SRE: Autonomous Incident Remediation Agent")
print(f">>> Memory Engine: Vectorize Hindsight | LLM: {ACTIVE_MODEL}")
print("=" * 70)

# Fresh profile incident-agent-v7 initializes the daemon cleanly with gemini-3.5-flash-lite
memory = HindsightEmbedded(
    profile="incident-agent-v7",
    llm_provider="gemini",
    llm_model=ACTIVE_MODEL,
    llm_api_key=GEMINI_API_KEY,
)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
BANK_ID = "production-incidents"


def ingest_history(file_path="incidents_history.json"):
    """Ingests historical post-mortems into Hindsight."""
    if not os.path.exists(file_path):
        seed_data = [
            {
                "title": "PostgreSQL connection pool exhaustion",
                "root_cause": "Payment microservice leaked connections, hitting maximum 100 limit.",
                "fix_command": "sudo systemctl restart pgbouncer && psql -c 'ALTER SYSTEM SET max_connections = 300;' && sudo systemctl reload postgresql",
            },
            {
                "title": "Redis memory saturation under spike traffic",
                "root_cause": "Default allkeys-lru eviction thrashing disk under burst load.",
                "fix_command": "redis-cli config set maxmemory-policy volatile-lru",
            },
        ]
    else:
        with open(file_path, "r") as f:
            seed_data = json.load(f)

    print(f"\n[INGESTION] Indexing {len(seed_data)} historical post-mortems into Hindsight...")
    for item in seed_data:
        content = (
            f"INCIDENT: {item['title']}\n"
            f"ROOT CAUSE: {item['root_cause']}\n"
            f"VERIFIED RUNBOOK FIX: {item['fix_command']}"
        )
        memory.retain(bank_id=BANK_ID, content=content)
    print("✓ Organizational memory bank loaded.\n")


def ask_stateless_llm(alert):
    """Shows what a generic, stateless LLM suggests without institutional memory."""
    prompt = f"You are an on-call SRE. Diagnose this alert and provide immediate bash fix commands in 2-3 bullet points:\n{alert}"
    chat = gemini_client.chats.create(model=ACTIVE_MODEL)
    response = chat.send_message(prompt)
    return response.text


def ask_hindsight_agent(alert):
    """Shows how Hindsight memory surfaces verified company runbooks."""
    print("🔍 [HINDSIGHT RECALL] Querying organizational memory bank...")
    past_memories = memory.recall(bank_id=BANK_ID, query=alert)

    recalled_text = ""
    if past_memories:
        print(f"✓ Found {len(past_memories)} relevant historical resolution facts!")
        for i, item in enumerate(past_memories[:3], 1):
            text_content = getattr(item, "text", str(item))
            print(f"   • Memory #{i}: {text_content[:85]}...")
            recalled_text += f"- {text_content}\n"
    else:
        print("⚠️ No prior incident memory found for this alert pattern.")

    prompt = f"""You are an expert on-call Site Reliability Engineer (SRE).
Diagnose the incoming alert. Prioritize the proven company runbook solution retrieved from memory and provide concise bash commands.

Incoming Alert:
{alert}

Relevant Historical Incidents & Runbooks:
{recalled_text if recalled_text else 'None available.'}

Provide:
1. Root Cause Diagnosis
2. Immediate Resolution Steps & Bash Commands"""

    chat = gemini_client.chats.create(model=ACTIVE_MODEL)
    response = chat.send_message(prompt)
    return response.text


if __name__ == "__main__":
    # Step 1: Ingest historical post-mortems
    ingest_history()

    test_alert = "CRITICAL ALERT: Postgres database rejecting connections, error says slots are fully occupied!"

    # Step 2: Test 1 - Stateless LLM
    print("\n" + "=" * 70)
    print("TEST 1: STATELESS LLM (WITHOUT HINDSIGHT MEMORY)")
    print("=" * 70)
    stateless_fix = ask_stateless_llm(test_alert)
    print(stateless_fix)
    print("\n[Notice: Generic baseline advice]\n")

    # Step 3: Test 2 - Hindsight memory-augmented response
    print("=" * 70)
    print("TEST 2: AUTONOMOUS SRE AGENT (WITH HINDSIGHT PERSISTENT MEMORY)")
    print("=" * 70)
    memory_fix = ask_hindsight_agent(test_alert)
    print("\n" + "-" * 25 + " REMEDIATION RUNBOOK " + "-" * 25)
    print(memory_fix)
    print("-" * 70 + "\n")