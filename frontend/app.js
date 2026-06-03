  import {
  CONFIG,
  getRecommendations as apiGetRecommendations,
  generateResume as apiGenerateResume,
  generateQuestions as apiGenerateQuestions,
  evaluateAnswer as apiEvaluateAnswer,
  generateFinalSummary as apiGenerateFinalSummary
} from './api.js';

(function () {
  'use strict';

  const STORAGE_KEY = 'genaihw2-ai-career-dashboard-v1';
  const DATA = CONFIG.USE_API ? {} : (window.DEMO_DATA || {});

  const steps = [
    { id: 1, label: 'Profile', sub: 'Experience input' },
    { id: 2, label: 'Jobs', sub: 'Recommendation' },
    { id: 3, label: 'Resume', sub: 'Optimizer' },
    { id: 4, label: 'Interview', sub: 'Simulation' },
    { id: 5, label: 'Summary', sub: 'Score report' }
  ];

  const defaultState = {
    step: 1,
    search: '',
    sort: 'score-desc',
    locationFilter: 'all',
    selectedJobId: null,
    questionIndex: 0,
    answers: {},
    evaluated: {},
    form: {
      name: 'Jane Doe',
      email: 'jane.doe@example.com',
      location: 'San Francisco, CA',
      workExperience: 'Senior Backend Engineer, Acme Corp (2021-present)\nDesigned and scaled distributed services handling 2M+ requests/day. Led migration to event-driven architecture, cutting p99 latency by 40%.\n\nSoftware Engineer, Startup Inc (2018-2021)\nBuilt the core REST API and CI/CD pipeline from scratch.',
      education: 'B.S. Computer Science, University of California, Berkeley (2018)',
      skills: 'Python, Go, PostgreSQL, Kubernetes, AWS, distributed systems, REST APIs',
      github: 'https://github.com/tiangolo',
      publications: 'https://arxiv.org/abs/1706.03762\nhttps://arxiv.org/abs/2507.06448',
      needs: 'Looking for a job in Taipei. Hoping for a salary of NT$40,000 or more.'
    }
  };

  let state = loadState();

  const app = document.getElementById('app');
  const stepperItems = document.getElementById('stepperItems');
  const progressFill = document.getElementById('progressFill');
  const toast = document.getElementById('toast');

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return structuredClone(defaultState);
      const parsed = JSON.parse(raw);
      return mergeDeep(structuredClone(defaultState), parsed);
    } catch (err) {
      return structuredClone(defaultState);
    }
  }

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function mergeDeep(target, source) {
    for (const key of Object.keys(source || {})) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        target[key] = mergeDeep(target[key] || {}, source[key]);
      } else {
        target[key] = source[key];
      }
    }
    return target;
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function truncate(value, max = 190) {
    const text = String(value || '').trim();
    if (text.length <= max) return text;
    return text.slice(0, max).trim() + '...';
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => toast.classList.remove('show'), 2600);
  }

 function getJobs() {
  if (CONFIG.USE_API) {
    return Array.isArray(DATA.rankedJobs) ? DATA.rankedJobs : [];
  }
  return Array.isArray(DATA.rankedJobs) ? DATA.rankedJobs : [];
}

  function getSelectedJob() {
    return getJobs().find(job => String(job.id) === String(state.selectedJobId)) || getJobs()[0] || null;
  }

  function getQuestions() {
    return DATA.interviewQuestions?.data?.questions || [];
  }

  function getEvaluationTemplate() {
    return DATA.evaluationResult?.data || {};
  }

  function getFinalSummary() {
    return DATA.finalSummary?.data || {};
  }

  function buildUserExperienceInput() {
    const f = state.form;
    return `## Basic info

Name: ${f.name}
Email: ${f.email}
Location: ${f.location}

## Work experience

${f.workExperience}

## Education

${f.education}

## Skills

${f.skills}

## GitHub

${f.github}

## Publications

${f.publications}`;
  }

  function buildProfilePayload() {
    return {
      user_experience_input: buildUserExperienceInput(),
      user_needs_input: state.form.needs,
      name: state.form.name,
      email: state.form.email,
      location: state.form.location,
      workExperience: state.form.workExperience,
      education: state.form.education,
      skills: state.form.skills,
      github: state.form.github,
      publications: state.form.publications,
      needs: state.form.needs
    };
  }

  function normalizeQuestions(result) {
    if (result?.data?.questions) return result;
    if (Array.isArray(result?.questions)) {
      return { success: true, error: null, data: result };
    }
    return result || { success: false, error: 'No questions returned', data: { questions: [] } };
  }

  function normalizeEvaluation(result) {
    return result?.data || result || {};
  }

  async function handleStepTransition(nextStep) {
    const targetStep = Number(nextStep);

if (!CONFIG.USE_API) {
  setStep(targetStep);
  return;
}

if (CONFIG.USE_API && targetStep > 1 && getJobs().length === 0 && targetStep !== 2) {
  showToast('Please generate job recommendations first.');
  return;
}

    try {
      if (targetStep === 2) {
        showToast('Calling backend: generating job recommendations...');
        const jobs = await apiGetRecommendations(buildProfilePayload());
        DATA.rankedJobs = Array.isArray(jobs) ? jobs : [];
        if (DATA.rankedJobs[0]) state.selectedJobId = DATA.rankedJobs[0].id;
      }

      if (targetStep === 3) {
        const selectedJob = getSelectedJob();
        if (!selectedJob) {
          showToast('Please select a job first.');
          return;
        }
        showToast('Calling backend: generating optimized resume...');
        DATA.resumeFinal = await apiGenerateResume({
          ...buildProfilePayload(),
          job: selectedJob,
          max_iter: 2,
          pass_score: 85
        });
      }

      if (targetStep === 4) {
        const selectedJob = getSelectedJob();
        if (!selectedJob) {
          showToast('Please select a job first.');
          return;
        }
        showToast('Calling backend: generating interview questions...');
        const questions = await apiGenerateQuestions({
          job: selectedJob,
          profile: DATA.resumeFinal || buildUserExperienceInput(),
          skills: state.form.skills.split(',').map(item => item.trim()).filter(Boolean),
          question_count: 5
        });
        DATA.interviewQuestions = normalizeQuestions(questions);
        state.questionIndex = 0;
      }

      if (targetStep === 5) {
        const selectedJob = getSelectedJob();
        const questions = getQuestions();
        const evaluatedAnswers = Object.keys(state.evaluated).map(key => {
          const index = Number(key);
          return {
            question: questions[index]?.question || '',
            answer: state.answers[index] || '',
            ...state.evaluated[key]
          };
        });

        if (selectedJob && evaluatedAnswers.length > 0) {
          showToast('Calling backend: generating final summary...');
          DATA.finalSummary = await apiGenerateFinalSummary({
            job: selectedJob,
            evaluated_answers: evaluatedAnswers
          });
        }
      }

      saveState();
      setStep(targetStep);
    } catch (error) {
      console.error(error);
      showToast(error.message || 'API call failed. Check backend server.');
    }
  }

  function getUniqueLocations() {
    const locations = [...new Set(getJobs().map(job => job.location).filter(Boolean))];
    return locations.sort((a, b) => a.localeCompare(b, 'zh-Hant'));
  }

  function setStep(nextStep) {
    state.step = Math.max(1, Math.min(5, Number(nextStep)));
    saveState();
    render();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function render() {
    renderStepper();
    const views = {
      1: renderProfileStep,
      2: renderJobsStep,
      3: renderResumeStep,
      4: renderInterviewStep,
      5: renderSummaryStep
    };
    app.innerHTML = views[state.step]();
    bindActiveViewEvents();
  }

  function renderStepper() {
    stepperItems.innerHTML = steps.map(step => {
      const status = step.id === state.step ? 'active' : step.id < state.step ? 'done' : '';
      return `
        <button class="step-item ${status}" type="button" data-stepper="${step.id}">
          <span class="step-num">${step.id < state.step ? '✓' : step.id}</span>
          <span>
            <span class="step-label">${step.label}</span>
            <span class="step-sub">${step.sub}</span>
          </span>
        </button>
      `;
    }).join('');

    const percent = ((state.step - 1) / (steps.length - 1)) * 100;
    progressFill.style.width = `${percent}%`;
  }

  function renderProfileStep() {
    const f = state.form;
    return `
      <div class="view panel-grid">
        <section class="card">
          <div class="card-head">
            <div>
              <span class="eyebrow">Step 1</span>
              <h2>User Profile Input</h2>
              <p>Input ini membentuk <strong>user_experience_input</strong> dan <strong>user_needs_input</strong> untuk recommendation system, resume optimizer, dan interview agent.</p>
            </div>
          </div>

          <form id="profileForm" class="form-grid">
            ${inputField('name', 'Name', f.name)}
            ${inputField('email', 'Email', f.email, 'email')}
            ${inputField('location', 'Current Location', f.location)}
            ${inputField('github', 'GitHub URL', f.github, 'url')}
            ${textareaField('workExperience', 'Work Experience', f.workExperience, 'full')}
            ${inputField('education', 'Education', f.education)}
            ${inputField('skills', 'Skills', f.skills)}
            ${textareaField('publications', 'Publication URLs', f.publications, 'full')}
            ${textareaField('needs', 'User Needs / Target Job Criteria', f.needs, 'full')}
          </form>

          <div class="panel-actions" style="margin-top: 22px;">
            <button class="primary-btn" type="button" data-next-step="2">Generate Job Recommendations</button>
            <button class="ghost-btn" type="button" id="fillSampleBtn">Fill Sample</button>
          </div>
        </section>

        <aside class="side-stack">
          <div class="mini-card">
            <h3>Backend Input Mapping</h3>
            <ul>
              <li>Recommendation: user experience + user needs.</li>
              <li>Resume: user experience + selected job.</li>
              <li>Interview Agent: selected job + optimized profile.</li>
            </ul>
          </div>
          <div class="mini-card">
            <h3>Session Snapshot</h3>
            <div class="stat-row">
              <div class="stat"><strong>${getJobs().length}</strong><span>Jobs loaded</span></div>
              <div class="stat"><strong>${getQuestions().length}</strong><span>Questions</span></div>
              <div class="stat"><strong>${getFinalSummary().average_score || '-'}</strong><span>Avg score</span></div>
            </div>
          </div>
          <div class="mini-card">
            <h3>Deployment Mode</h3>
            <p>Current mode: <strong>${CONFIG.USE_API ? 'Realtime API' : 'Demo Data'}</strong>. Demo mode reads embedded backend outputs; API mode calls FastAPI endpoints in realtime.</p>
          </div>
        </aside>
      </div>
    `;
  }

  function inputField(name, label, value, type = 'text') {
    return `
      <div class="field">
        <label for="${name}">${label}</label>
        <input id="${name}" name="${name}" type="${type}" value="${escapeHtml(value)}" autocomplete="off" />
      </div>
    `;
  }

  function textareaField(name, label, value, extraClass = '') {
    return `
      <div class="field ${extraClass}">
        <label for="${name}">${label}</label>
        <textarea id="${name}" name="${name}">${escapeHtml(value)}</textarea>
      </div>
    `;
  }

  function renderJobsStep() {
    const selectedJob = getSelectedJob();
    const locations = getUniqueLocations();
    const filteredJobs = getFilteredJobs();

    return `
      <div class="view panel-grid">
        <section class="card">
          <div class="card-head">
            <div>
              <span class="eyebrow">Step 2</span>
              <h2>Ranked Job Recommendations</h2>
              <p>Choose one job to continue to resume optimization and interview simulation.</p>
            </div>
            <div class="inline-actions">
              <button class="ghost-btn small" type="button" data-next-step="1">Back</button>
              <button class="primary-btn small" type="button" data-next-step="3" ${selectedJob ? '' : 'disabled'}>Continue</button>
            </div>
          </div>

          <div class="jobs-toolbar">
            <input id="jobSearch" type="search" placeholder="Search title, company, skill..." value="${escapeHtml(state.search)}" />
            <select id="locationFilter">
              <option value="all">All locations</option>
              ${locations.map(loc => `<option value="${escapeHtml(loc)}" ${state.locationFilter === loc ? 'selected' : ''}>${escapeHtml(loc)}</option>`).join('')}
            </select>
            <select id="sortSelect">
              <option value="score-desc" ${state.sort === 'score-desc' ? 'selected' : ''}>Score high</option>
              <option value="score-asc" ${state.sort === 'score-asc' ? 'selected' : ''}>Score low</option>
              <option value="title" ${state.sort === 'title' ? 'selected' : ''}>Title A-Z</option>
            </select>
          </div>

          <div class="jobs-grid">
            ${filteredJobs.map(renderJobCard).join('') || '<div class="empty-state">No jobs found. Try another search.</div>'}
          </div>
        </section>

        <aside class="side-stack selected-job-panel">
          <div class="mini-card">
            <h3>Selected Job</h3>
            ${selectedJob ? renderSelectedJobSummary(selectedJob) : '<p>No selected job yet.</p>'}
          </div>
          <div class="mini-card">
            <h3>Top Match Logic</h3>
            <div class="timeline">
              <div class="timeline-item"><span class="timeline-dot">1</span><div class="timeline-body"><strong>Profile</strong><p>${escapeHtml(truncate(state.form.skills, 90))}</p></div></div>
              <div class="timeline-item"><span class="timeline-dot">2</span><div class="timeline-body"><strong>Needs</strong><p>${escapeHtml(truncate(state.form.needs, 90))}</p></div></div>
              <div class="timeline-item"><span class="timeline-dot">3</span><div class="timeline-body"><strong>Ranking</strong><p>Jobs are ordered by backend-generated score and verdict.</p></div></div>
            </div>
          </div>
        </aside>
      </div>
    `;
  }

  function getFilteredJobs() {
    const query = state.search.trim().toLowerCase();
    return getJobs()
      .filter(job => {
        const text = [job.job_title, job.company_name, job.location, job.salary, job.description, job.verdict].join(' ').toLowerCase();
        const matchesQuery = !query || text.includes(query);
        const matchesLocation = state.locationFilter === 'all' || job.location === state.locationFilter;
        return matchesQuery && matchesLocation;
      })
      .sort((a, b) => {
        if (state.sort === 'score-asc') return (a.score || 0) - (b.score || 0);
        if (state.sort === 'title') return String(a.job_title || '').localeCompare(String(b.job_title || ''), 'zh-Hant');
        return (b.score || 0) - (a.score || 0);
      });
  }

  function renderJobCard(job) {
    const isSelected = String(job.id) === String(state.selectedJobId);
    const score = Number(job.score || 0);
    const width = Math.max(0, Math.min(100, score * 10));
    const skillTags = extractTags(job.description).slice(0, 5);

    return `
      <article class="job-card ${isSelected ? 'selected' : ''}">
        <div class="job-top">
          <div>
            <h3>${escapeHtml(job.job_title)}</h3>
            <div class="job-meta">${escapeHtml(job.company_name)}<br>${escapeHtml(job.location)} · ${escapeHtml(job.experience)}</div>
          </div>
          <div class="score-badge">${score.toFixed(1)}</div>
        </div>
        <div class="score-bar" style="--score-width:${width}%"><span></span></div>
        <p class="job-verdict">${escapeHtml(job.verdict || 'No verdict available.')}</p>
        <div class="tag-list">
          <span class="tag">${escapeHtml(job.salary || 'Salary N/A')}</span>
          ${skillTags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
        </div>
        <div class="job-actions">
          <button class="chip-btn ${isSelected ? 'active' : ''}" type="button" data-select-job="${escapeHtml(job.id)}">${isSelected ? 'Selected' : 'Select Job'}</button>
          <a class="chip-btn" href="${escapeHtml(job.link || '#')}" target="_blank" rel="noreferrer">Open Link</a>
        </div>
      </article>
    `;
  }

  function extractTags(text) {
    const tags = ['Python', 'FastAPI', 'Flask', 'Django', 'Docker', 'Kubernetes', 'AWS', 'GCP', 'React', 'Vue', 'REST', 'CI/CD', 'SQL', 'Redis'];
    const lower = String(text || '').toLowerCase();
    return tags.filter(tag => lower.includes(tag.toLowerCase()));
  }

  function renderSelectedJobSummary(job) {
    return `
      <p class="muted">${escapeHtml(job.company_name)} · ${escapeHtml(job.location)}</p>
      <h3>${escapeHtml(job.job_title)}</h3>
      <div class="match-meter"><div><strong>${Number(job.score || 0).toFixed(1)}</strong><br><span>match score</span></div></div>
      <p style="margin-top: 16px;">${escapeHtml(job.verdict || '')}</p>
      <p class="muted"><strong>Salary:</strong> ${escapeHtml(job.salary || 'N/A')}</p>
    `;
  }

  function renderResumeStep() {
    const selectedJob = getSelectedJob();
    const resumeHtml = markdownToHtml(DATA.resumeFinal || 'Resume output is not available.');

    return `
      <div class="view resume-layout">
        <aside class="side-stack">
          <div class="mini-card">
            <span class="eyebrow">Step 3</span>
            <h3>Resume Optimizer</h3>
            <p>The frontend displays <strong>resume_final.md</strong> directly, matching the backend instruction.</p>
            <div class="inline-actions" style="margin-top: 16px;">
              <button class="ghost-btn small" type="button" data-next-step="2">Back</button>
              <button class="primary-btn small" type="button" data-next-step="4">Start Interview</button>
            </div>
          </div>
          <div class="mini-card">
            <h3>Target Job</h3>
            ${selectedJob ? renderSelectedJobSummary(selectedJob) : '<p>No selected job yet.</p>'}
          </div>
          <div class="mini-card">
            <h3>Resume Actions</h3>
            <div class="inline-actions">
              <button class="chip-btn" type="button" id="copyResumeBtn">Copy Resume</button>
              <button class="chip-btn" type="button" id="downloadResumeBtn">Download MD</button>
            </div>
          </div>
        </aside>

        <section class="resume-preview">
          ${resumeHtml}
        </section>
      </div>
    `;
  }

  function markdownToHtml(markdown) {
  const lines = String(markdown || '').replace(/\r/g, '').split('\n');
  const out = [];
  let inList = false;
  let titleConsumed = false;

  function closeList() {
    if (inList) {
      out.push('</ul>');
      inList = false;
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      closeList();
      continue;
    }

    // Hide markdown horizontal rules like --- or ***
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(line)) {
      closeList();
      continue;
    }

    if (line.startsWith('### ')) {
      closeList();
      out.push(`<h3>${inlineMd(line.slice(4))}</h3>`);
    } else if (line.startsWith('## ')) {
      closeList();
      out.push(`<h2>${inlineMd(line.slice(3))}</h2>`);
    } else if (line.startsWith('# ')) {
      closeList();
      out.push(`<h1>${inlineMd(line.slice(2))}</h1>`);
    } else if (line.startsWith('* ') || line.startsWith('- ')) {
      if (!inList) {
        out.push('<ul>');
        inList = true;
      }
      out.push(`<li>${inlineMd(line.slice(2))}</li>`);
    } else if (!titleConsumed && !line.includes('|') && line.length < 80) {
      closeList();
      out.push(`<h1>${inlineMd(line)}</h1>`);
      titleConsumed = true;
    } else {
      closeList();
      out.push(`<p>${inlineMd(line)}</p>`);
    }
  }

  closeList();
  return out.join('\n');
}

  function inlineMd(value) {
    return escapeHtml(value)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>');
  }

  function renderInterviewStep() {
    const questions = getQuestions();
    const selectedJob = getSelectedJob();
    const q = questions[state.questionIndex] || questions[0];
    const currentAnswer = state.answers[state.questionIndex] || '';
    const currentEval = state.evaluated[state.questionIndex];

    if (!q) {
      return `<div class="view card empty-state">No interview questions found.</div>`;
    }

    return `
      <div class="view interview-layout">
        <section class="question-card">
          <div class="card-head">
            <div>
              <span class="eyebrow">Step 4</span>
              <h2>Interview Simulation</h2>
              <p>Question ${state.questionIndex + 1} of ${questions.length} for ${escapeHtml(selectedJob?.job_title || DATA.interviewQuestions?.data?.job_title || 'selected job')}.</p>
            </div>
            <div class="inline-actions">
              <button class="ghost-btn small" type="button" data-next-step="3">Back</button>
              <button class="primary-btn small" type="button" data-next-step="5">Final Summary</button>
            </div>
          </div>

          <div class="question-meta">
            <span class="tag">${escapeHtml(q.type)}</span>
            <span class="tag">${escapeHtml(q.difficulty)}</span>
            <span class="tag">${escapeHtml(DATA.interviewQuestions?.data?.candidate_level || 'Candidate')}</span>
          </div>

          <div class="question-text">${escapeHtml(q.question)}</div>

          <div class="answer-box field">
            <label for="answerInput">Your Answer</label>
            <textarea id="answerInput" placeholder="Write your answer here...">${escapeHtml(currentAnswer)}</textarea>
          </div>

          <div class="panel-actions" style="margin-top: 18px;">
            <button class="ghost-btn" type="button" id="prevQuestionBtn" ${state.questionIndex === 0 ? 'disabled' : ''}>Previous</button>
            <button class="primary-btn" type="button" id="evaluateBtn">Evaluate Answer</button>
            <button class="ghost-btn" type="button" id="nextQuestionBtn" ${state.questionIndex >= questions.length - 1 ? 'disabled' : ''}>Next</button>
          </div>

          ${currentEval ? renderFeedback(currentEval) : ''}
        </section>

        <aside class="side-stack">
          <div class="mini-card">
            <h3>Interview Focus</h3>
            <div class="tag-list">
              ${(DATA.interviewQuestions?.data?.interview_focus || []).map(item => `<span class="tag">${escapeHtml(item)}</span>`).join('')}
            </div>
          </div>
          <div class="mini-card">
            <h3>Answer Progress</h3>
            <div class="timeline">
              ${questions.map((question, index) => `
                <div class="timeline-item">
                  <span class="timeline-dot">${state.evaluated[index] ? '✓' : index + 1}</span>
                  <div class="timeline-body">
                    <strong>${escapeHtml(question.type)}</strong>
                    <p>${escapeHtml(truncate(question.question, 82))}</p>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </aside>
      </div>
    `;
  }

  function renderFeedback(data) {
    return `
      <div class="feedback-card">
        <h3>Evaluation Result: ${escapeHtml(data.score ?? '-')} / 10</h3>
        <p>${escapeHtml(data.feedback || '')}</p>
        <div class="two-col">
          <div>
            <strong>Strengths</strong>
            <ul>${(data.strengths || []).slice(0, 4).map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
          </div>
          <div>
            <strong>Weaknesses</strong>
            <ul>${(data.weaknesses || []).slice(0, 4).map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
          </div>
        </div>
        ${data.better_answer ? `<p><strong>Better answer:</strong> ${escapeHtml(data.better_answer)}</p>` : ''}
      </div>
    `;
  }

  function renderSummaryStep() {
    const summary = getFinalSummary();
    const answeredCount = Object.keys(state.answers).filter(key => state.answers[key]).length;
    const totalQuestions = summary.total_questions || getQuestions().length || 0;

    return `
      <div class="view card">
        <div class="card-head">
          <div>
            <span class="eyebrow">Step 5</span>
            <h2>Final Interview Summary</h2>
            <p>Dashboard report based on backend final_summary.json and your current session progress.</p>
          </div>
          <div class="inline-actions">
            <button class="ghost-btn small" type="button" data-next-step="4">Back</button>
            <button class="primary-btn small" type="button" id="exportBtnInline">Export Session</button>
          </div>
        </div>

        <div class="summary-grid">
          <div class="result-card"><strong>${escapeHtml(summary.average_score ?? '-')}</strong><span>Average score</span></div>
          <div class="result-card"><strong>${escapeHtml(summary.overall_level ?? '-')}</strong><span>Overall level</span></div>
          <div class="result-card"><strong>${escapeHtml(summary.recommendation ?? '-')}</strong><span>Recommendation</span></div>
        </div>

        <div class="result-card" style="margin-bottom: 18px;">
          <h3>Overall Summary</h3>
          <p class="muted" style="line-height: 1.75;">${escapeHtml(summary.summary || 'No summary available.')}</p>
          <div class="stat-row">
            <div class="stat"><strong>${answeredCount}</strong><span>Your answers</span></div>
            <div class="stat"><strong>${totalQuestions}</strong><span>Total questions</span></div>
            <div class="stat"><strong>${escapeHtml(getSelectedJob()?.score ?? '-')}</strong><span>Job match</span></div>
          </div>
        </div>

        <div class="two-col">
          <div class="result-card list-card">
            <h3>Strong Areas</h3>
            <ul>${(summary.strong_areas || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
          </div>
          <div class="result-card list-card">
            <h3>Weak Areas</h3>
            <ul>${(summary.weak_areas || []).map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
          </div>
        </div>

        <div class="result-card" style="margin-top: 18px;">
          <h3>Suggested Improvement Plan</h3>
          <div class="timeline">
            <div class="timeline-item"><span class="timeline-dot">1</span><div class="timeline-body"><strong>Structure answers with STAR</strong><p>Use Situation, Task, Action, Result to make behavioral answers more convincing.</p></div></div>
            <div class="timeline-item"><span class="timeline-dot">2</span><div class="timeline-body"><strong>Add technical depth</strong><p>Include security, monitoring, testing, and failure recovery details.</p></div></div>
            <div class="timeline-item"><span class="timeline-dot">3</span><div class="timeline-body"><strong>Connect every answer to business impact</strong><p>Mention measurable outcomes such as latency, cost, reliability, or user impact.</p></div></div>
          </div>
        </div>
      </div>
    `;
  }

  function bindActiveViewEvents() {
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
      profileForm.addEventListener('input', event => {
        const target = event.target;
        if (!target.name) return;
        state.form[target.name] = target.value;
        saveState();
      });
    }

    const jobSearch = document.getElementById('jobSearch');
    if (jobSearch) {
      jobSearch.addEventListener('input', event => {
        state.search = event.target.value;
        saveState();
        render();
      });
    }

    const locationFilter = document.getElementById('locationFilter');
    if (locationFilter) {
      locationFilter.addEventListener('change', event => {
        state.locationFilter = event.target.value;
        saveState();
        render();
      });
    }

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
      sortSelect.addEventListener('change', event => {
        state.sort = event.target.value;
        saveState();
        render();
      });
    }

    const answerInput = document.getElementById('answerInput');
    if (answerInput) {
      answerInput.addEventListener('input', event => {
        state.answers[state.questionIndex] = event.target.value;
        saveState();
      });
    }
  }

  document.addEventListener('click', async event => {
    const nextButton = event.target.closest('[data-next-step]');
    if (nextButton) {
      await handleStepTransition(nextButton.dataset.nextStep);
      return;
    }

    const stepper = event.target.closest('[data-stepper]');
if (stepper) {
  await handleStepTransition(stepper.dataset.stepper);
  return;
}

    const selectJob = event.target.closest('[data-select-job]');
    if (selectJob) {
      state.selectedJobId = selectJob.dataset.selectJob;
      saveState();
      showToast('Job selected. Continue to resume optimization.');
      render();
      return;
    }

    if (event.target.id === 'resetBtn') {
  localStorage.removeItem(STORAGE_KEY);

  DATA.rankedJobs = [];
  DATA.resumeFinal = '';
  DATA.interviewQuestions = { success: true, error: null, data: { questions: [] } };
  DATA.finalSummary = { success: true, error: null, data: {} };

  state = structuredClone(defaultState);
  showToast('Session reset successfully.');
  render();
  return;
}

    if (event.target.id === 'fillSampleBtn') {
      state.form = structuredClone(defaultState.form);
      saveState();
      showToast('Sample profile restored.');
      render();
      return;
    }

    if (event.target.id === 'copyResumeBtn') {
      copyText(DATA.resumeFinal || '').then(() => showToast('Resume copied to clipboard.'));
      return;
    }

    if (event.target.id === 'downloadResumeBtn') {
      downloadFile('resume_final.md', DATA.resumeFinal || '', 'text/markdown');
      return;
    }

    if (event.target.id === 'prevQuestionBtn') {
      state.questionIndex = Math.max(0, state.questionIndex - 1);
      saveState();
      render();
      return;
    }

    if (event.target.id === 'nextQuestionBtn') {
      state.questionIndex = Math.min(getQuestions().length - 1, state.questionIndex + 1);
      saveState();
      render();
      return;
    }

    if (event.target.id === 'evaluateBtn') {
      const input = document.getElementById('answerInput');
      const answer = input ? input.value.trim() : '';
      if (!answer) {
        showToast('Please write an answer before evaluation.');
        return;
      }

      const questions = getQuestions();
      const question = questions[state.questionIndex]?.question || '';
      state.answers[state.questionIndex] = answer;

      if (CONFIG.USE_API) {
        try {
          showToast('Calling backend: evaluating answer...');
          const result = await apiEvaluateAnswer({
            job: getSelectedJob(),
            profile: DATA.resumeFinal || buildUserExperienceInput(),
            skills: state.form.skills.split(',').map(item => item.trim()).filter(Boolean),
            question,
            answer
          });
          state.evaluated[state.questionIndex] = normalizeEvaluation(result);
          showToast('Answer evaluated by realtime AI.');
        } catch (error) {
          console.error(error);
          showToast(error.message || 'Evaluation API failed.');
          return;
        }
      } else {
        state.evaluated[state.questionIndex] = createEvaluationForAnswer(answer);
        showToast('Answer evaluated using demo evaluation output.');
      }

      saveState();
      render();
      return;
    }

    if (event.target.id === 'exportBtn' || event.target.id === 'exportBtnInline') {
      exportSession();
    }
  });

  function createEvaluationForAnswer(answer) {
    const template = structuredClone(getEvaluationTemplate());
    const lengthBonus = answer.length > 350 ? 0.6 : answer.length > 180 ? 0.3 : 0;
    const keywordBonus = ['security', 'monitor', 'test', 'scale', 'latency', 'kafka', 'docker', 'kubernetes', 'aws']
      .some(word => answer.toLowerCase().includes(word)) ? 0.4 : 0;
    const score = Math.min(10, Number(template.score || 7) + lengthBonus + keywordBonus);
    return {
      ...template,
      score: Number(score.toFixed(1))
    };
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    textarea.remove();
  }

  function downloadFile(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function exportSession() {
    const payload = {
      exportedAt: new Date().toISOString(),
      profile: state.form,
      selectedJob: getSelectedJob(),
      answers: state.answers,
      evaluated: state.evaluated,
      finalSummary: getFinalSummary()
    };
    downloadFile('ai-career-session.json', JSON.stringify(payload, null, 2), 'application/json');
    showToast('Session exported.');
  }

  render();
})();
