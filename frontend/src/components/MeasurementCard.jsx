import React from 'react';
import { Stethoscope, ExternalLink, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

function getStatusBadge(status, isCritical) {
  if (isCritical || status === 'CRITICAL_LOW' || status === 'CRITICAL_HIGH') {
    return (
      <span className="badge CRITICAL_LOW">
        <AlertTriangle size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-top' }} />
        CRITICAL ALERT
      </span>
    );
  }
  if (status === 'LOW') {
    return (
      <span className="badge LOW">
        <AlertCircle size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-top' }} />
        LOW
      </span>
    );
  }
  if (status === 'HIGH') {
    return (
      <span className="badge HIGH">
        <AlertCircle size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-top' }} />
        HIGH
      </span>
    );
  }
  return (
    <span className="badge NORMAL">
      <CheckCircle size={14} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-top' }} />
      NORMAL
    </span>
  );
}

export default function MeasurementCard({ measurement }) {
  const m = measurement;
  const refText = (m.ref_min !== null && m.ref_max !== null)
    ? `${m.ref_min} - ${m.ref_max} ${m.unit}`
    : 'Standard interval not specified';

  return (
    <div className="measurement-card">
      <div className="card-top">
        <div className="test-title">
          <h3>{m.canonical_name}</h3>
          <span>Report label: {m.test_name}</span>
        </div>
        <div>
          {getStatusBadge(m.status, m.is_critical)}
        </div>
      </div>

      <div className="measurement-details">
        <div>
          <span style={{ fontSize: '0.85rem', color: '#64748b', display: 'block' }}>Measured Result</span>
          <span className="value-highlight">{m.measured_value} {m.unit}</span>
        </div>
        <div>
          <span style={{ fontSize: '0.85rem', color: '#64748b', display: 'block' }}>Reference Interval</span>
          <span className="ref-range">{refText}</span>
        </div>
      </div>

      {m.explanation && (
        <div className="explanation-text">
          {m.explanation}
        </div>
      )}

      {m.questions_for_doctor && m.questions_for_doctor.length > 0 && (
        <details className="doctor-questions">
          <summary>
            <Stethoscope size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
            Questions to Ask Your Doctor ({m.questions_for_doctor.length})
          </summary>
          <ul>
            {m.questions_for_doctor.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </details>
      )}

      {m.citations && m.citations.length > 0 && (
        <span className="citation-tag">
          Authoritative Reference:{' '}
          <a href={m.citations[0]} target="_blank" rel="noreferrer">
            {m.citations[0]} <ExternalLink size={12} style={{ display: 'inline', verticalAlign: 'middle' }} />
          </a>
        </span>
      )}
    </div>
  );
}
