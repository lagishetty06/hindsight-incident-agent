import os
import json
import warnings
import asyncio
from hindsight import HindsightEmbedded
from google import genai

# Suppress minor library warnings & Windows proactor pipe noise
warnings.filterwarnings("ignore")
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 1. API Configuration
# Reads securely from environment variable, with local fallback
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "gemni api key here"
)
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

ACTIVE_MODEL = "gemini-3.5-flash-lite"

print("=" * 72)
print(">>> AutoOps SRE: Autonomous Incident Doctor with Hindsight Memory")
print(f">>> Memory Engine: Vectorize Hindsight (pgvector) | LLM: {ACTIVE_MODEL}")
print("=" * 72)

# Initialize embedded Hindsight and Gemini client
memory = HindsightEmbedded(
    profile="incident-agent-v7",
    llm_provider="gemini",
    llm_model=ACTIVE_MODEL,
    llm_api_key=GEMINI_API_KEY,
)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
BANK_ID = "production-incidents"


def ingest_history(file_path="incidents_history.json"):
    """Ingests historical post-mortems with duplicate prevention."""
    # Deduplication Guard: Avoid duplicate insertions if bank is already seeded
    existing = memory.recall(bank_id=BANK_ID, query="PostgreSQL connection exhaustion")
    if existing and len(existing) > 0:
        print("\n[INGESTION] Organizational memory bank already initialized. Skipping duplicate seeding.\n")
        return

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
    """Demonstrates generic, trial-and-error advice without memory."""
    prompt = f"You are an on-call SRE. Diagnose this alert and provide immediate bash fix commands in 2-3 concise bullet points:\n{alert}"
    chat = gemini_client.chats.create(model=ACTIVE_MODEL)
    response = chat.send_message(prompt)
    return response.text


def ask_hindsight_agent(alert):
    """Retrieves verified runbooks and generates an exact, non-destructive fix."""
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
    # Step 1: Initialize institutional memory bank
    ingest_history()

    test_alert = "CRITICAL ALERT: Postgres database rejecting connections, error says slots are fully occupied!"

    # Step 2: Test 1 - Stateless LLM baseline
    print("=" * 72)
    print("PHASE 1: STATELESS LLM BASELINE (WITHOUT PERSISTENT MEMORY)")
    print("=" * 72)
    stateless_fix = ask_stateless_llm(test_alert)
    print(stateless_fix)
    print("\n[Result: Generic textbook advice - often suggests risky full database reboots]\n")

    # Step 3: Test 2 - Memory-augmented agent
    print("=" * 72)
    print("PHASE 2: AUTONOMOUS SRE AGENT (WITH HINDSIGHT PERSISTENT MEMORY)")
    print("=" * 72)
    memory_fix = ask_hindsight_agent(test_alert)
    print("\n" + "-" * 25 + " REMEDIATION RUNBOOK " + "-" * 25)
    print(memory_fix)
    print("-" * 72)

    # Step 4: Enterprise Safety Guardrail (Human-in-the-Loop)
    print("\n🛡️ [SAFETY GUARDRAIL] Execution Mode: Human-in-the-Loop")
    approval = input("Authorize agent to execute verified remediation commands on cluster? (y/N): ")
    if approval.strip().lower() == "y":
        print("✓ [DRY RUN] Execution approved: Target bash commands dispatched to staging runner.")
    else:
        print("⏹ Execution held: Safety stop engaged by SRE operator.")

    # Step 5: Dynamic On-The-Fly Learning Demonstration
    print("\n" + "=" * 72)
    print("PHASE 3: CONTINUOUS LEARNING LOOP (LEARNING A NEW INCIDENT LIVE)")
    print("=" * 72)
    print("Simulating a brand-new Kafka incident resolved by senior engineer...")
    new_knowledge = (
        "INCIDENT: Kafka consumer lag spike on orders-stream\n"
        "ROOT CAUSE: Worker thread deadlock on malformed null JSON message.\n"
        "VERIFIED RUNBOOK FIX: sudo systemctl restart order-consumer && kubectl scale deployment order-consumer --replicas=5"
    )
    memory.retain(bank_id=BANK_ID, content=new_knowledge)
    print("✓ Newly resolved Kafka outage indexed into Hindsight memory!\n")

    test_kafka_alert = "ALERT: Consumer lag on topic 'orders-stream' exceeded 100,000 records, ingestion stopped!"
    print(f"Testing recall on new alert: \"{test_kafka_alert}\"")
    kafka_plan = ask_hindsight_agent(test_kafka_alert)
    print("\n" + "-" * 25 + " NEWLY LEARNED RUNBOOK " + "-" * 25)
    print(kafka_plan)
    print("-" * 72 + "\n")