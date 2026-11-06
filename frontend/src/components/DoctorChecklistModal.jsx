import React, { useState } from 'react';
import { ClipboardList, Copy, Check } from 'lucide-react';

export default function DoctorChecklistModal({ measurements }) {
  const [copied, setCopied] = useState(false);

  const attentionItems = measurements.filter(
    (m) => m.status !== 'NORMAL' && m.questions_for_doctor && m.questions_for_doctor.length > 0
  );

  if (attentionItems.length === 0) return null;

  const checklistText = attentionItems.map((m) => {
    const questions = m.questions_for_doctor.map((q) => `  - [ ] ${q}`).join('\n');
    return `${m.canonical_name} (${m.measured_value} ${m.unit} - ${m.status}):\n${questions}`;
  }).join('\n\n');

  const handleCopy = () => {
    navigator.clipboard.writeText(checklistText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '18px', marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ClipboardList size={20} color="#1e3a8a" />
          <h3 style={{ fontSize: '1.1rem', color: '#1e3a8a', margin: 0 }}>Doctor Discussion Checklist</h3>
        </div>
        <button 
          onClick={handleCopy}
          className="btn-primary" 
          style={{ padding: '6px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? 'Copied to Clipboard' : 'Copy Checklist'}
        </button>
      </div>
      <p style={{ fontSize: '0.88rem', color: '#64748b', marginBottom: '12px' }}>
        Bring these questions to your next appointment regarding the biomarkers requiring attention:
      </p>
      <pre style={{ 
        background: 'white', 
        padding: '14px', 
        borderRadius: '8px', 
        border: '1px solid #e2e8f0', 
        fontSize: '0.85rem', 
        fontFamily: 'monospace', 
        whiteSpace: 'pre-wrap', 
        color: '#334155' 
      }}>
        {checklistText}
      </pre>
    </div>
  );
}
