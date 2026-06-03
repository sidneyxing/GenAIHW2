// frontend/api.js
// Switch between static demo data and real backend API.

export const CONFIG = {
  // false = use demoData.js / window.DEMO_DATA
  // true  = call api_server.py endpoints
  USE_API: false,
  API_BASE_URL: 'http://localhost:8000'
};

export function getDemoData() {
  return window.DEMO_DATA || {};
}

async function post(endpoint, payload) {
  const res = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {})
  });

  let body = null;
  try {
    body = await res.json();
  } catch (_) {
    body = null;
  }

  if (!res.ok) {
    const message = body?.detail || body?.error || `API error: ${res.status}`;
    throw new Error(message);
  }

  return body;
}

export async function getRecommendations(payload) {
  if (!CONFIG.USE_API) return getDemoData().rankedJobs || [];
  const result = await post('/recommend', payload);
  return result.rankedJobs || result.data || result.jobs || result;
}

export async function generateResume(payload) {
  if (!CONFIG.USE_API) return getDemoData().resumeFinal || '';
  const result = await post('/resume', payload);
  return result.resumeFinal || result.resume || result.data?.resumeFinal || result.data || '';
}

export async function generateQuestions(payload) {
  if (!CONFIG.USE_API) return getDemoData().interviewQuestions || {};
  return await post('/interview/questions', payload);
}

export async function evaluateAnswer(payload) {
  if (!CONFIG.USE_API) return getDemoData().evaluationResult || {};
  return await post('/interview/evaluate', payload);
}

export async function generateFinalSummary(payload) {
  if (!CONFIG.USE_API) return getDemoData().finalSummary || {};
  return await post('/interview/summary', payload);
}
