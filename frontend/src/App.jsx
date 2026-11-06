import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import MeasurementCard from './components/MeasurementCard';
import DoctorChecklistModal from './components/DoctorChecklistModal';
import { fetchSamples, fetchSampleReport, analyzeTextReport, uploadPdfReport } from './services/api';
import { FileText, Upload, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';

export default function App() {
  const [language, setLanguage] = useState('en');
  const [activeTab, setActiveTab] = useState('sample');
  const [samples, setSamples] = useState([]);
  const [selectedSampleId, setSelectedSampleId] = useState('cbc_anemia');
  const [rawText, setRawText] = useState('');
  const [pdfFile, setPdfFile] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load sample list on mount
  useEffect(() => {
    fetchSamples()
      .then((data) => {
        setSamples(data);
        // Load initial default sample
        loadSample('cbc_anemia', language);
      })
      .catch((err) => {
        console.warn('API error loading samples:', err);
      });
  }, []);

  // Reload when language changes if report is loaded
  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    if (activeTab === 'sample' && selectedSampleId) {
      loadSample(selectedSampleId, newLang);
    }
  };

  const loadSample = async (sampleId, lang) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSampleReport(sampleId, lang);
      setReport(data);
      setSelectedSampleId(sampleId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeText = async () => {
    if (!rawText.trim()) {
      setError('Please enter or paste report text.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeTextReport(rawText, language);
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadPdf = async () => {
    if (!pdfFile) {
      setError('Please choose a PDF file first.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await uploadPdfReport(pdfFile, language);
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Metrics calculation
  const measurements = report?.measurements || [];
  const totalCount = measurements.length;
  const normalCount = measurements.filter((m) => m.status === 'NORMAL').length;
  const attentionCount = measurements.filter((m) => m.status === 'LOW' || m.status === 'HIGH').length;
  const criticalCount = measurements.filter((m) => m.is_critical).length;

  return (
    <div className="container">
      <Header language={language} onLanguageChange={handleLanguageChange} />

      {/* Input Options Card */}
      <div className="input-card">
        <div className="tabs-header">
          <button 
            className={`tab-btn ${activeTab === 'sample' ? 'active' : ''}`}
            onClick={() => setActiveTab('sample')}
          >
            <Sparkles size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
            Try Clinical Samples
          </button>
          <button 
            className={`tab-btn ${activeTab === 'pdf' ? 'active' : ''}`}
            onClick={() => setActiveTab('pdf')}
          >
            <Upload size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
            Upload PDF
          </button>
          <button 
            className={`tab-btn ${activeTab === 'text' ? 'active' : ''}`}
            onClick={() => setActiveTab('text')}
          >
            <FileText size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
            Paste Report Text
          </button>
        </div>

        {/* Tab 1: Samples */}
        {activeTab === 'sample' && (
          <div>
            <div className="sample-grid">
              {samples.map((s) => (
                <div 
                  key={s.id} 
                  className={`sample-chip ${selectedSampleId === s.id ? 'selected' : ''}`}
                  onClick={() => loadSample(s.id, language)}
                >
                  <h4>{s.name}</h4>
                  <p>{s.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 2: PDF Upload */}
        {activeTab === 'pdf' && (
          <div>
            <div className="file-dropzone">
              <input 
                type="file" 
                accept="application/pdf"
                id="pdf-upload"
                style={{ display: 'none' }}
                onChange={(e) => setPdfFile(e.target.files[0])}
              />
              <label htmlFor="pdf-upload" style={{ cursor: 'pointer' }}>
                <Upload size={36} color="#2563eb" style={{ marginBottom: 8 }} />
                <p style={{ fontWeight: 600, color: '#1e293b' }}>
                  {pdfFile ? pdfFile.name : 'Click to select or drag and drop a PDF report'}
                </p>
                <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
                  Digital blood reports (CBC, Lipid, Metabolic, Thyroid)
                </span>
              </label>
            </div>
            <div style={{ marginTop: 14, textAlign: 'right' }}>
              <button 
                className="btn-primary" 
                onClick={handleUploadPdf}
                disabled={!pdfFile || loading}
              >
                {loading ? 'Processing...' : 'Analyze Uploaded PDF'}
              </button>
            </div>
          </div>
        )}

        {/* Tab 3: Paste Text */}
        {activeTab === 'text' && (
          <div>
            <textarea
              style={{
                width: '100%',
                height: 120,
                borderRadius: 8,
                border: '1px solid #cbd5e1',
                padding: 12,
                fontSize: '0.9rem',
                fontFamily: 'inherit',
                marginBottom: 10
              }}
              placeholder={`Example:\nHemoglobin: 10.4 g/dL (12.0 - 15.0)\nPlatelet Count: 210000 /uL (150000 - 450000)\nTotal Cholesterol: 245 mg/dL (0 - 200)`}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
            />
            <div style={{ textAlign: 'right' }}>
              <button 
                className="btn-primary" 
                onClick={handleAnalyzeText}
                disabled={loading}
              >
                {loading ? 'Analyzing...' : 'Analyze Report Text'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', padding: '12px 16px', borderRadius: 8, color: '#991b1b', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Loading Spinner */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#64748b' }}>
          <RefreshCw size={28} className="spin" style={{ display: 'inline', animation: 'spin 1s linear infinite' }} />
          <p style={{ marginTop: 8, fontWeight: 500 }}>Extracting parameters & verifying reference ranges...</p>
          <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* Results Dashboard */}
      {!loading && report && measurements.length > 0 && (
        <div>
          {/* Metrics Row */}
          <div className="metrics-row">
            <div className="metric-tile">
              <div className="label">Total Parameters</div>
              <div className="value" style={{ color: '#0f172a' }}>{totalCount}</div>
            </div>
            <div className="metric-tile">
              <div className="label">Normal Range</div>
              <div className="value" style={{ color: '#059669' }}>{normalCount}</div>
            </div>
            <div className="metric-tile">
              <div className="label">Attention Needed</div>
              <div className="value" style={{ color: '#d97706' }}>{attentionCount}</div>
            </div>
            <div className="metric-tile">
              <div className="label">Urgent Alerts</div>
              <div className="value" style={{ color: '#dc2626' }}>{criticalCount}</div>
            </div>
          </div>

          {/* Executive Summary */}
          {report.summary && (
            <div className={`summary-box ${report.overall_status}`}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 4 }}>
                {report.overall_status === 'CRITICAL' ? '🚨 Clinical Attention Required' : 'Executive Overview'}
              </h3>
              <p style={{ fontSize: '0.95rem' }}>{report.summary}</p>
            </div>
          )}

          {/* Measurements Cards */}
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#1e293b', marginBottom: 16 }}>
              Biomarker Breakdown
            </h2>
            {measurements.map((m, idx) => (
              <MeasurementCard key={idx} measurement={m} />
            ))}
          </div>

          {/* Doctor Discussion Checklist */}
          <DoctorChecklistModal measurements={measurements} />
        </div>
      )}
    </div>
  );
}
