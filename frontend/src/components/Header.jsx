import React from 'react';
import { ShieldCheck, HeartPulse, Globe } from 'lucide-react';

export default function Header({ language, onLanguageChange }) {
  return (
    <header>
      <div className="header-nav">
        <div className="brand">
          <div className="brand-icon">
            <HeartPulse size={24} />
          </div>
          <div>
            <h1>BloodLab AI Explainer</h1>
            <p>Deterministic verification • MedlinePlus RAG • Responsible AI</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Globe size={18} color="#64748b" />
          <select 
            className="lang-select" 
            value={language} 
            onChange={(e) => onLanguageChange(e.target.value)}
          >
            <option value="en">English (US)</option>
            <option value="hi">हिंदी (Hindi)</option>
            <option value="mr">मराठी (Marathi)</option>
          </select>
        </div>
      </div>

      <div className="privacy-banner">
        <ShieldCheck size={20} color="#166534" />
        <div>
          <strong>Ephemeral In-Memory Processing:</strong> Your health records are parsed purely in-memory. Zero files or personal patient data are written to disk or permanent databases.
        </div>
      </div>
    </header>
  );
}
