const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function fetchSamples() {
  const res = await fetch(`${API_BASE_URL}/api/samples`);
  if (!res.ok) throw new Error('Failed to fetch sample panels');
  return res.json();
}

export async function fetchSampleReport(sampleId, language = 'en') {
  const res = await fetch(`${API_BASE_URL}/api/samples/${sampleId}?language=${language}`);
  if (!res.ok) throw new Error(`Failed to load sample: ${res.statusText}`);
  return res.json();
}

export async function analyzeTextReport(rawText, language = 'en') {
  const res = await fetch(`${API_BASE_URL}/api/analyze-text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_text: rawText, language })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Analysis failed');
  }
  return res.json();
}

export async function uploadPdfReport(file, language = 'en') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language);

  const res = await fetch(`${API_BASE_URL}/api/upload-pdf`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'PDF processing failed');
  }
  return res.json();
}
