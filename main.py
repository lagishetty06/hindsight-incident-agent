import os
import warnings
from hindsight import HindsightEmbedded
from google import genai

# Suppress minor library warnings for a clean terminal demo
warnings.filterwarnings("ignore")

# 1. API Configuration
GEMINI_API_KEY = "paste api key here"
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
ACTIVE_MODEL = "gemini-2.5-flash"

print("=" * 65)
print(">>> AutoOps SRE: Autonomous Incident Doctor with Hindsight Memory")
print(f">>> Memory Engine: Vectorize Hindsight | LLM: {ACTIVE_MODEL}")
print("=" * 65)

memory = HindsightEmbedded(
    profile="incident-agent-gemini",
    llm_provider="gemini",
    llm_model=ACTIVE_MODEL,
    llm_api_key=GEMINI_API_KEY,
)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
BANK_ID = "production-incidents"

def retain_resolution(incident_title, root_cause, fix_command):
    """Stores a verified incident resolution in Hindsight memory."""
    knowledge = (
        f"INCIDENT: {incident_title}\n"
        f"ROOT CAUSE: {root_cause}\n"
        f"VERIFIED RUNBOOK FIX: {fix_command}"
    )
    print(f"\n[LEARNING] Ingesting verified incident resolution into Hindsight...")
    memory.retain(bank_id=BANK_ID, content=knowledge)
    print("✓ Successfully indexed into semantic memory bank!\n")

def diagnose_alert(incoming_alert):
    """Recalls past incident memory and generates production-ready fix."""
    print("\n" + "=" * 65)
    print(f"🚨 [NEW INCOMING ALERT]: {incoming_alert}")
    print("=" * 65)
    
    print("🔍 [HINDSIGHT RECALL] Querying organizational memory bank...")
    past_memories = memory.recall(bank_id=BANK_ID, query=incoming_alert)
    
    recalled_text = ""
    if past_memories:
        print(f"✓ Found {len(past_memories)} relevant historical resolution facts!")
        for i, item in enumerate(past_memories[:4], 1):
            text_content = getattr(item, 'text', str(item))
            print(f"   • Memory #{i}: {text_content[:85]}...")
            recalled_text += f"- {text_content}\n"
    else:
        print("⚠️ No prior incident memory found for this alert pattern.")

    prompt = f"""You are an expert on-call Site Reliability Engineer (SRE).
Diagnose the incoming alert. If past company incident memories are available, prioritize that proven runbook solution and give exact bash commands.

Incoming Alert:
{incoming_alert}

Relevant Historical Incidents & Runbooks:
{recalled_text if recalled_text else 'None available.'}

Provide:
1. Root Cause Diagnosis
2. Immediate Resolution Steps & Bash Commands"""

    print("\n⚡ [AGENT REASONING] Generating remediation plan...")
    chat = gemini_client.chats.create(model=ACTIVE_MODEL)
    response = chat.send_message(prompt)

    print("\n" + "-" * 25 + " REMEDIATION RUNBOOK " + "-" * 25)
    print(response.text)
    print("-" * 71 + "\n")

if __name__ == "__main__":
    print("\n[STEP 1] Seeding institutional runbooks into Hindsight...")
    retain_resolution(
        incident_title="PostgreSQL connection exhaustion 'FATAL: remaining connection slots are reserved'",
        root_cause="Leaked pool connections from payment microservice hitting 100 max_connections limit.",
        fix_command="Run 'sudo systemctl restart pgbouncer' to cycle idle clients, then update postgresql.conf to max_connections=300 and reload."
    )
    retain_resolution(
        incident_title="Redis OOM and CPU spike at 100% during traffic surges",
        root_cause="Default allkeys-lru eviction thrashing disk under burst load.",
        fix_command="Execute 'redis-cli config set maxmemory-policy volatile-lru' and double the allocated RAM buffer."
    )

    print("\n[STEP 2] Simulating incoming real-time alert (Postgres)...")
    test_alert_1 = "CRITICAL ALERT: Postgres database rejecting connections, error says slots are fully occupied!"
    diagnose_alert(test_alert_1)

    print("\n[STEP 3] Dynamically teaching agent a new incident resolution...")
    retain_resolution(
        incident_title="Kafka consumer lag spike on 'orders-stream'",
        root_cause="Stuck worker thread deadlocked on unhandled null JSON payload.",
        fix_command="sudo systemctl restart order-consumer && kubectl scale deployment order-consumer --replicas=5"
    )

    print("\n[STEP 4] Simulating incoming real-time alert for newly learned event (Kafka)...")
    test_alert_2 = "WARNING: Order consumer lag exceeds 50,000 messages, processing halted!"
    diagnose_alert(test_alert_2)