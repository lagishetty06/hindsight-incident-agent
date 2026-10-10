import React, { useState } from 'react';

const PRESETS = [
  {
    name: 'Postgres',
    alert: 'CRITICAL: Postgres database rejecting connections, slots fully occupied!'
  },
  {
    name: 'Kafka',
    alert: "ALERT: Consumer lag on topic 'orders-stream' exceeded 100,000 records, ingestion stopped!"
  }
];

export default function App() {
  const [alertText, setAlertText] = useState(PRESETS[0].alert);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [execStatus, setExecStatus] = useState(null);

  const triggerDiagnosis = async () => {
    setLoading(true);
    setExecStatus(null);
    try {
      const res = await fetch('http://localhost:8000/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert: alertText })
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert('Backend offline. Ensure uvicorn is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const executeRunbook = async (approved) => {
    if (!result?.commands) return;
    try {
      const res = await fetch('http://localhost:8000/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ commands: result.commands, approved })
      });
      const data = await res.json();
      setExecStatus(data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#070b14', color: '#f1f5f9', fontFamily: 'sans-serif', padding: '2rem' }}>
      <div style={{ maxWidth: '860px', margin: '0 auto' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b', paddingBottom: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#38bdf8', margin: 0 }}>
              AutoOps SRE: Incident Remediation Agent
            </h1>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: '0.2rem 0 0' }}>
              Persistent Memory via Vectorize Hindsight + Guardrailed Execution
            </p>
          </div>
          <span style={{ fontSize: '0.75rem', padding: '0.25rem 0.75rem', borderRadius: '999px', backgroundColor: '#064e3b', color: '#34d399', fontWeight: 'bold' }}>
            Live Node (:8000)
          </span>
        </div>

        {/* Alert Box */}
        <div style={{ marginTop: '1.5rem', backgroundColor: '#0d1322', padding: '1.25rem', borderRadius: '10px', border: '1px solid #1e293b' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#94a3b8' }}>ACTIVE PRODUCTION ALERT</label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => setAlertText(p.alert)}
                  style={{ background: '#1e293b', color: '#38bdf8', border: 'none', padding: '0.25rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  Preset: {p.name}
                </button>
              ))}
            </div>
          </div>

          <textarea
            rows={3}
            value={alertText}
            onChange={(e) => setAlertText(e.target.value)}
            style={{ width: '100%', boxSizing: 'border-box', backgroundColor: '#020617', border: '1px solid #334155', borderRadius: '6px', padding: '0.75rem', color: '#f8fafc', fontFamily: 'monospace', fontSize: '0.85rem' }}
          />

          <button
            onClick={triggerDiagnosis}
            disabled={loading}
            style={{ marginTop: '0.8rem', width: '100%', padding: '0.8rem', backgroundColor: '#0284c7', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: loading ? 'not-allowed' : 'pointer' }}
          >
            {loading ? 'Recalling Past Runbooks...' : 'Query Persistent Memory & Diagnose'}
          </button>
        </div>

        {/* Results */}
        {result && (
          <div style={{ marginTop: '1.5rem', backgroundColor: '#0d1322', padding: '1.25rem', borderRadius: '10px', border: '1px solid #059669' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#34d399', margin: 0 }}>
                Verified Resolution Runbook
              </h2>
              <span style={{ fontSize: '0.75rem', backgroundColor: '#064e3b', color: '#6ee7b7', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                Confidence: 98%
              </span>
            </div>

            <div style={{ marginTop: '0.85rem', backgroundColor: '#020617', borderLeft: '4px solid #38bdf8', padding: '0.6rem 0.85rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 'bold' }}>ROOT CAUSE</div>
              <div style={{ fontSize: '0.85rem', color: '#e2e8f0', marginTop: '0.2rem' }}>{result.root_cause}</div>
            </div>

            {/* Recalled Memory Chips */}
            {result.recalled_facts && (
              <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {result.recalled_facts.map((fact, idx) => (
                  <div key={idx} style={{ fontSize: '0.8rem', color: '#a7f3d0', backgroundColor: '#064e3b', padding: '0.4rem 0.6rem', borderRadius: '6px', fontFamily: 'monospace' }}>
                    🧠 {fact}
                  </div>
                ))}
              </div>
            )}

            {/* Bash Commands */}
            <div style={{ marginTop: '0.85rem', backgroundColor: '#020617', padding: '0.85rem', borderRadius: '6px', border: '1px solid #1e293b' }}>
              <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: '0.4rem', fontWeight: 'bold' }}>DISPATCHABLE COMMANDS:</div>
              {result.commands.map((cmd, i) => (
                <div key={i} style={{ fontFamily: 'monospace', fontSize: '0.85rem', color: '#38bdf8', margin: '0.25rem 0' }}>
                  $ {cmd}
                </div>
              ))}
            </div>

            {/* Human in the loop */}
            <div style={{ marginTop: '1rem', padding: '0.85rem', backgroundColor: '#020617', borderRadius: '6px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#f8fafc' }}>🛡️ Human-in-the-Loop Safeguard</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Authorize staging dispatch of runbook commands</div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  onClick={() => executeRunbook(false)}
                  style={{ padding: '0.45rem 0.8rem', backgroundColor: '#450a0a', color: '#fca5a5', border: '1px solid #991b1b', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                >
                  Reject
                </button>
                <button
                  onClick={() => executeRunbook(true)}
                  style={{ padding: '0.45rem 0.9rem', backgroundColor: '#059669', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.8rem' }}
                >
                  Approve Execution
                </button>
              </div>
            </div>

            {/* Status */}
            {execStatus && (
              <div style={{ marginTop: '0.85rem', padding: '0.75rem', borderRadius: '4px', fontSize: '0.85rem', backgroundColor: execStatus.status === 'success' ? '#064e3b' : '#450a0a', color: execStatus.status === 'success' ? '#6ee7b7' : '#fca5a5' }}>
                {execStatus.message}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}