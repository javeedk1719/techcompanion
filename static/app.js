// ============================================
// STATE
// ============================================
let state = {
  userId: null,
  currentAssessmentId: null,
  currentAssessmentTopic: null,
};

function apiBase() {
  return document.getElementById('apiBase').value.replace(/\/$/, '');
}

async function api(path, options = {}) {
  const res = await fetch(apiBase() + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

function setStatus(id, msg, ok = true) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = 'status ' + (ok ? 'ok' : 'err');
}

function csv(str) {
  return str.split(',').map(s => s.trim()).filter(Boolean);
}

// ============================================
// NAV
// ============================================
document.querySelectorAll('.navitem').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.navitem').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('view-' + btn.dataset.view).classList.add('active');
  });
});

// ============================================
// 01 — SETUP
// ============================================
document.getElementById('btnCreateUser').addEventListener('click', async () => {
  const name = document.getElementById('su_name').value.trim();
  const email = document.getElementById('su_email').value.trim();
  if (!name || !email) return setStatus('statusCreateUser', 'Enter a name and email first.', false);

  try {
    const user = await api('/users/', {
      method: 'POST',
      body: JSON.stringify({ name, email }),
    });
    state.userId = user.id;
    document.getElementById('activeUserId').textContent = `#${user.id} — ${user.name}`;
    setStatus('statusCreateUser', `Created student #${user.id}. Now fill in the profile below.`, true);
  } catch (e) {
    setStatus('statusCreateUser', 'Failed: ' + e.message, false);
  }
});

document.getElementById('btnSaveProfile').addEventListener('click', async () => {
  if (!state.userId) return setStatus('statusSaveProfile', 'Create a student first.', false);

  const payload = {
    goal: document.getElementById('pf_goal').value.trim(),
    current_level: document.getElementById('pf_level').value,
    interests: csv(document.getElementById('pf_interests').value),
    known_skills: csv(document.getElementById('pf_skills').value),
    available_time_per_day: document.getElementById('pf_time').value.trim() || '1 hour',
    resource_preference: document.getElementById('pf_resource').value,
  };

  try {
    await api(`/users/${state.userId}/profile`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    setStatus('statusSaveProfile', 'Profile saved. Head to the Daily Brief tab.', true);
  } catch (e) {
    setStatus('statusSaveProfile', 'Failed: ' + e.message, false);
  }
});

// ============================================
// 02 — DAILY BRIEF
// ============================================
document.getElementById('btnIngest').addEventListener('click', async () => {
  setStatus('statusBrief', 'Pulling latest tech from sources…');
  try {
    const r = await api('/techbrief/ingest', { method: 'POST' });
    setStatus('statusBrief', `Ingested ${r.ingested} new item(s).`, true);
    loadBrief();
  } catch (e) {
    setStatus('statusBrief', 'Failed: ' + e.message, false);
  }
});

document.getElementById('btnLoadBrief').addEventListener('click', loadBrief);

async function loadBrief() {
  setStatus('statusBrief', 'Loading brief…');
  try {
    const items = await api('/techbrief/latest?limit=10');
    renderBrief(items);
    setStatus('statusBrief', `Showing ${items.length} item(s).`, true);
  } catch (e) {
    setStatus('statusBrief', 'Failed: ' + e.message, false);
  }
}

function renderBrief(items) {
  const list = document.getElementById('briefList');
  list.innerHTML = '';
  if (items.length === 0) {
    list.innerHTML = '<p class="lede">No items yet — click "Pull latest tech" first.</p>';
    return;
  }
  items.forEach(item => {
    const div = document.createElement('div');
    div.className = 'brief-item';
    div.innerHTML = `
      <div class="brief-item-top">
        <p class="brief-title">${escapeHtml(item.title)}</p>
        <span class="difficulty-badge diff-${item.difficulty}">${item.difficulty}</span>
      </div>
      <p class="brief-summary">${escapeHtml(item.summary)}</p>
      <div class="brief-tags">${item.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}</div>
      <div class="item-btn-row">
        <button class="btn why-btn" data-id="${item.id}">Why should I care?</button>
      </div>
      <div class="why-result" id="why-${item.id}"></div>
    `;
    list.appendChild(div);
  });

  document.querySelectorAll('.why-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!state.userId) return alert('Create a student and profile first (Step 01).');
      const id = btn.dataset.id;
      const target = document.getElementById('why-' + id);
      target.innerHTML = '<p class="lede">Thinking…</p>';
      try {
        const r = await api(`/techbrief/${state.userId}/why-care/${id}`);
        target.innerHTML = `
          <div class="brief-why">
            <b>Why it matters to you:</b> ${escapeHtml(r.why_it_matters)}<br/>
            <b>Difficulty for you:</b> ${escapeHtml(r.difficulty_for_you)}<br/>
            <b>Learn next?</b> ${r.should_learn_next ? 'Yes' : 'Not yet'} — ${escapeHtml(r.reason)}
          </div>`;
      } catch (e) {
        target.innerHTML = `<p class="status err">Failed: ${e.message}</p>`;
      }
    });
  });
}

document.getElementById('btnWhatsNext').addEventListener('click', async () => {
  if (!state.userId) return setStatus('statusBrief', 'Create a student and profile first.', false);
  setStatus('statusBrief', 'Ranking recommendations for this student…');
  try {
    const results = await api(`/techbrief/${state.userId}/whats-next?limit=5`);
    const list = document.getElementById('briefList');
    list.innerHTML = '<p class="lede" style="margin-bottom:10px;">Recommended next, personalized to this student:</p>';
    results.forEach(r => {
      const div = document.createElement('div');
      div.className = 'brief-item';
      div.innerHTML = `
        <p class="brief-title">${escapeHtml(r.title)}</p>
        <div class="brief-why">
          <b>Why:</b> ${escapeHtml(r.why_it_matters)}<br/>
          <b>Difficulty for you:</b> ${escapeHtml(r.difficulty_for_you)}
        </div>`;
      list.appendChild(div);
    });
    setStatus('statusBrief', `Found ${results.length} recommendation(s).`, true);
  } catch (e) {
    setStatus('statusBrief', 'Failed: ' + e.message, false);
  }
});

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str ?? '';
  return d.innerHTML;
}

// ============================================
// 03 — CHAT
// ============================================
document.getElementById('btnSendChat').addEventListener('click', sendChat);
document.getElementById('chatMessage').addEventListener('keydown', e => {
  if (e.key === 'Enter') sendChat();
});

async function sendChat() {
  if (!state.userId) return setStatus('statusChat', 'Create a student and profile first.', false);
  const topic = document.getElementById('chatTopic').value.trim();
  const message = document.getElementById('chatMessage').value.trim();
  if (!topic || !message) return setStatus('statusChat', 'Enter a topic and a message.', false);

  appendChatMsg('user', message);
  document.getElementById('chatMessage').value = '';
  setStatus('statusChat', 'Thinking…');

  try {
    const r = await api('/chat/', {
      method: 'POST',
      body: JSON.stringify({ user_id: state.userId, topic, message }),
    });
    appendChatMsg('assistant', r.reply);
    setStatus('statusChat', '', true);
  } catch (e) {
    setStatus('statusChat', 'Failed: ' + e.message, false);
  }
}

function appendChatMsg(role, content) {
  const box = document.getElementById('chatbox');
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = content;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

// ============================================
// 04 — ASSESSMENT
// ============================================
document.getElementById('btnGenQuiz').addEventListener('click', async () => {
  if (!state.userId) return setStatus('statusQuiz', 'Create a student and profile first.', false);
  const topic = document.getElementById('as_topic').value.trim();
  const num = parseInt(document.getElementById('as_num').value, 10) || 3;
  if (!topic) return setStatus('statusQuiz', 'Enter a topic.', false);

  setStatus('statusQuiz', 'Generating quiz…');
  document.getElementById('quizResult').style.display = 'none';
  try {
    const r = await api('/assessment/generate', {
      method: 'POST',
      body: JSON.stringify({ user_id: state.userId, topic, num_questions: num }),
    });
    state.currentAssessmentId = r.assessment_id;
    state.currentAssessmentTopic = r.topic;
    renderQuiz(r.questions);
    setStatus('statusQuiz', `Quiz ready — ${r.questions.length} question(s).`, true);
  } catch (e) {
    setStatus('statusQuiz', 'Failed: ' + e.message, false);
  }
});

function renderQuiz(questions) {
  const form = document.getElementById('quizForm');
  form.innerHTML = '';
  questions.forEach((q, qi) => {
    const div = document.createElement('div');
    div.className = 'quiz-q';
    div.innerHTML = `
      <p class="qtext">${qi + 1}. ${escapeHtml(q.question)}</p>
      ${q.options.map((opt, oi) => `
        <label class="quiz-opt">
          <input type="radio" name="q${qi}" value="${oi}" />
          ${escapeHtml(opt)}
        </label>
      `).join('')}
    `;
    form.appendChild(div);
  });
  document.getElementById('btnSubmitQuiz').style.display = questions.length ? 'inline-block' : 'none';
}

document.getElementById('btnSubmitQuiz').addEventListener('click', async () => {
  const form = document.getElementById('quizForm');
  const qCount = form.querySelectorAll('.quiz-q').length;
  const answers = [];
  for (let i = 0; i < qCount; i++) {
    const checked = form.querySelector(`input[name="q${i}"]:checked`);
    answers.push(checked ? parseInt(checked.value, 10) : -1);
  }

  setStatus('statusQuiz', 'Grading…');
  try {
    const r = await api('/assessment/submit', {
      method: 'POST',
      body: JSON.stringify({ assessment_id: state.currentAssessmentId, answers }),
    });
    renderQuizResult(r);
    setStatus('statusQuiz', 'Graded.', true);
  } catch (e) {
    setStatus('statusQuiz', 'Failed: ' + e.message, false);
  }
});

function renderQuizResult(r) {
  const box = document.getElementById('quizResult');
  box.style.display = 'block';
  box.innerHTML = `<h3>Score: ${r.score}%</h3>` + r.feedback.map(f => `
    <div class="feedback-row ${f.is_correct ? 'correct' : 'incorrect'}">
      <b>${escapeHtml(f.question)}</b><br/>
      Your answer: ${escapeHtml(f.your_answer)}<br/>
      Correct answer: ${escapeHtml(f.correct_answer)}<br/>
      <span style="color:var(--paper-dim)">${escapeHtml(f.explanation)}</span>
    </div>
  `).join('');
}

// ============================================
// 05 — DASHBOARD
// ============================================
document.getElementById('btnLoadDashboard').addEventListener('click', async () => {
  if (!state.userId) return alert('Create a student first (Step 01).');
  try {
    const d = await api(`/dashboard/${state.userId}`);
    const grid = document.getElementById('statGrid');
    grid.innerHTML = `
      <div class="stat-box"><div class="stat-num">${d.items_viewed}</div><div class="stat-label">Items viewed</div></div>
      <div class="stat-box"><div class="stat-num">${d.items_completed}</div><div class="stat-label">Completed</div></div>
      <div class="stat-box"><div class="stat-num">${d.assessments_taken}</div><div class="stat-label">Assessments</div></div>
      <div class="stat-box"><div class="stat-num">${d.average_score}%</div><div class="stat-label">Avg score</div></div>
    `;
    document.getElementById('nudgeText').textContent = d.nudge || '';
    document.getElementById('nudgeText').style.display = d.nudge ? 'block' : 'none';
  } catch (e) {
    alert('Failed: ' + e.message);
  }
});

document.getElementById('btnBuildChallenge').addEventListener('click', async () => {
  if (!state.userId) return alert('Create a student first (Step 01).');
  const topic = document.getElementById('bc_topic').value.trim();
  if (!topic) return alert('Enter a topic.');
  const target = document.getElementById('buildChallengeResult');
  target.textContent = 'Thinking of a project…';
  try {
    const r = await api(`/dashboard/${state.userId}/build-challenge?topic=${encodeURIComponent(topic)}`);
    target.textContent = r.project_suggestion;
  } catch (e) {
    target.textContent = 'Failed: ' + e.message;
  }
});
