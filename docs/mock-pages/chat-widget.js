/*
 * Caritas chat widget — a reusable 1-on-1 chat modal.
 *
 * Include with <script src="chat-widget.js"></script> on any authenticated
 * page, then call:
 *   CaritasChat.openByReporter(reporterId, reporterName)  // staff -> reporter
 *   CaritasChat.openByThread(threadId)
 *   CaritasChat.unreadByVillage()  // -> Promise<{ [village_id]: unreadCount }>
 *
 * Polls the open thread every 30s; matches the dashboard polling cadence.
 */
(function () {
  const API = 'http://localhost:8000';
  const POLL_MS = 30000;

  function token() {
    return localStorage.getItem('access_token');
  }

  function headers(json) {
    const h = { Authorization: 'Bearer ' + token() };
    if (json) h['Content-Type'] = 'application/json';
    return h;
  }

  function currentUserId() {
    try {
      return JSON.parse(atob(token().split('.')[1])).sub;
    } catch (e) {
      return null;
    }
  }

  function formatTime(iso) {
    return new Date(iso).toLocaleString('en-GB', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  // ── Inject styles ──────────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    .cc-overlay {
      position: fixed; inset: 0; z-index: 100;
      background: rgba(44,44,44,0.45);
      backdrop-filter: blur(2px);
      display: none; align-items: center; justify-content: center;
      padding: 1.5rem;
    }
    .cc-overlay.open { display: flex; }
    .cc-modal {
      width: min(440px, 100%); max-height: 80vh;
      background: var(--caritas-white, #fff);
      border-radius: 24px;
      box-shadow: 0 30px 70px rgba(44,44,44,0.3);
      display: flex; flex-direction: column; overflow: hidden;
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }
    .cc-head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 1.1rem 1.35rem;
      border-bottom: 1px solid var(--caritas-border, rgba(44,44,44,0.12));
      flex-shrink: 0;
    }
    .cc-title {
      font-family: Athelas, "Iowan Old Style", Georgia, serif;
      font-size: 1.2rem; font-weight: 700;
      color: var(--caritas-text, #2C2C2C);
    }
    .cc-sub {
      font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em;
      text-transform: uppercase; color: rgba(44,44,44,0.45); margin-top: 0.15rem;
    }
    .cc-close {
      background: var(--caritas-cream, #F9F6F3); border: none; cursor: pointer;
      width: 32px; height: 32px; border-radius: 50%;
      font-size: 0.95rem; color: rgba(44,44,44,0.6);
      display: grid; place-items: center; transition: all 150ms;
    }
    .cc-close:hover { background: var(--caritas-red, #B10017); color: #fff; }
    .cc-body {
      flex: 1; overflow-y: auto; padding: 1.25rem;
      background: var(--caritas-cream, #F9F6F3);
      display: flex; flex-direction: column; gap: 0.7rem;
    }
    .cc-empty {
      margin: auto; text-align: center; color: rgba(44,44,44,0.4);
      font-size: 0.9rem; max-width: 24ch; line-height: 1.5;
    }
    .cc-msg { max-width: 78%; display: flex; flex-direction: column; gap: 0.2rem; }
    .cc-msg.mine { align-self: flex-end; align-items: flex-end; }
    .cc-msg.theirs { align-self: flex-start; align-items: flex-start; }
    .cc-bubble {
      padding: 0.6rem 0.85rem; border-radius: 16px;
      font-size: 0.9rem; line-height: 1.4; white-space: pre-wrap;
      word-break: break-word;
    }
    .cc-msg.mine .cc-bubble {
      background: var(--caritas-red, #B10017); color: #fff;
      border-bottom-right-radius: 4px;
    }
    .cc-msg.theirs .cc-bubble {
      background: #fff; color: var(--caritas-text, #2C2C2C);
      border: 1px solid var(--caritas-border, rgba(44,44,44,0.12));
      border-bottom-left-radius: 4px;
    }
    .cc-meta {
      font-size: 0.68rem; color: rgba(44,44,44,0.4);
      padding: 0 0.35rem;
    }
    .cc-foot {
      display: flex; gap: 0.6rem; align-items: flex-end;
      padding: 0.9rem 1.1rem;
      border-top: 1px solid var(--caritas-border, rgba(44,44,44,0.12));
      flex-shrink: 0;
    }
    .cc-input {
      flex: 1; resize: none; max-height: 120px;
      padding: 0.65rem 0.9rem;
      border: 1px solid var(--caritas-border, rgba(44,44,44,0.12));
      border-radius: 18px; font-size: 0.9rem; font-family: inherit;
      color: var(--caritas-text, #2C2C2C); outline: none;
    }
    .cc-input:focus { border-color: var(--caritas-red, #B10017); }
    .cc-send {
      flex-shrink: 0; border: none; cursor: pointer;
      background: var(--caritas-red, #B10017); color: #fff;
      border-radius: 50%; width: 42px; height: 42px;
      font-size: 1.1rem; display: grid; place-items: center;
      transition: background 150ms;
    }
    .cc-send:hover { background: var(--caritas-red-dark, #8F0012); }
    .cc-send:disabled { opacity: 0.5; cursor: default; }

    /* Reusable chat trigger button + unread badge */
    .cc-chat-btn {
      position: relative; display: inline-grid; place-items: center;
      width: 34px; height: 34px; border-radius: 50%;
      border: 1px solid var(--caritas-border, rgba(44,44,44,0.12));
      background: #fff; cursor: pointer; font-size: 1rem; line-height: 1;
      color: rgba(44,44,44,0.6); transition: all 150ms; text-decoration: none;
    }
    .cc-chat-btn:hover {
      border-color: var(--caritas-red, #B10017);
      color: var(--caritas-red, #B10017);
    }
    .cc-badge {
      position: absolute; top: -5px; right: -5px;
      min-width: 18px; height: 18px; padding: 0 4px;
      border-radius: 9px; background: var(--caritas-red, #B10017);
      color: #fff; font-size: 0.65rem; font-weight: 700;
      display: grid; place-items: center; border: 2px solid #fff;
      box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
  `;
  document.head.appendChild(style);

  // ── Inject modal DOM ───────────────────────────────────────────
  const overlay = document.createElement('div');
  overlay.className = 'cc-overlay';
  overlay.innerHTML = `
    <div class="cc-modal" role="dialog" aria-modal="true">
      <div class="cc-head">
        <div>
          <div class="cc-title" id="cc-title">Chat</div>
          <div class="cc-sub" id="cc-sub">Conversation</div>
        </div>
        <button class="cc-close" id="cc-close" title="Close">&#x2715;</button>
      </div>
      <div class="cc-body" id="cc-body"></div>
      <div class="cc-foot">
        <textarea class="cc-input" id="cc-input" rows="1" placeholder="Type a message…"></textarea>
        <button class="cc-send" id="cc-send" title="Send">&#x27A4;</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const elBody = overlay.querySelector('#cc-body');
  const elInput = overlay.querySelector('#cc-input');
  const elSend = overlay.querySelector('#cc-send');
  const elTitle = overlay.querySelector('#cc-title');
  const elSub = overlay.querySelector('#cc-sub');

  let activeThreadId = null;
  let pollTimer = null;
  const me = currentUserId();

  function render(detail) {
    elTitle.textContent = detail.reporter_name || 'Chat';
    if (!detail.messages || detail.messages.length === 0) {
      elBody.innerHTML = '<div class="cc-empty">No messages yet. Say hello to start the conversation.</div>';
      return;
    }
    elBody.innerHTML = detail.messages
      .map((m) => {
        const mine = m.sender_id === me;
        return (
          '<div class="cc-msg ' + (mine ? 'mine' : 'theirs') + '">' +
          '<div class="cc-bubble">' + escapeHtml(m.content) + '</div>' +
          '<div class="cc-meta">' +
          (mine ? '' : escapeHtml(m.sender_name) + ' · ') +
          formatTime(m.created_at) +
          '</div>' +
          '</div>'
        );
      })
      .join('');
    elBody.scrollTop = elBody.scrollHeight;
  }

  async function loadThread() {
    if (!activeThreadId) return;
    const detail = await fetch(API + '/chat/threads/' + activeThreadId, {
      headers: headers(),
    }).then((r) => r.json());
    render(detail);
  }

  function startPolling() {
    stopPolling();
    pollTimer = setInterval(loadThread, POLL_MS);
  }

  function stopPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = null;
  }

  function open(detail) {
    activeThreadId = detail.id;
    elSub.textContent = 'Conversation';
    render(detail);
    overlay.classList.add('open');
    elInput.value = '';
    elInput.focus();
    startPolling();
  }

  function close() {
    overlay.classList.remove('open');
    stopPolling();
    activeThreadId = null;
    if (typeof window.__ccOnClose === 'function') window.__ccOnClose();
  }

  async function send() {
    const content = elInput.value.trim();
    if (!content || !activeThreadId) return;
    elSend.disabled = true;
    try {
      await fetch(API + '/chat/threads/' + activeThreadId + '/messages', {
        method: 'POST',
        headers: headers(true),
        body: JSON.stringify({ content }),
      });
      elInput.value = '';
      elInput.style.height = 'auto';
      await loadThread();
    } finally {
      elSend.disabled = false;
      elInput.focus();
    }
  }

  // ── Events ─────────────────────────────────────────────────────
  overlay.querySelector('#cc-close').addEventListener('click', close);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });
  elSend.addEventListener('click', send);
  elInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
  elInput.addEventListener('input', () => {
    elInput.style.height = 'auto';
    elInput.style.height = Math.min(elInput.scrollHeight, 120) + 'px';
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('open')) close();
  });

  // ── Public API ─────────────────────────────────────────────────
  async function openByReporter(reporterId, reporterName) {
    const detail = await fetch(
      API + '/chat/threads/by-reporter/' + reporterId,
      { headers: headers() }
    ).then((r) => r.json());
    if (reporterName) detail.reporter_name = reporterName;
    open(detail);
  }

  async function openByThread(threadId) {
    const detail = await fetch(API + '/chat/threads/' + threadId, {
      headers: headers(),
    }).then((r) => r.json());
    open(detail);
  }

  async function listThreads() {
    return fetch(API + '/chat/threads', { headers: headers() }).then((r) =>
      r.ok ? r.json() : []
    );
  }

  async function unreadByVillage() {
    const threads = await listThreads();
    const map = {};
    threads.forEach((t) => {
      if (!t.village_id) return;
      map[t.village_id] = (map[t.village_id] || 0) + t.unread_count;
    });
    return map;
  }

  async function unreadByReporter() {
    const threads = await listThreads();
    const map = {};
    threads.forEach((t) => {
      map[t.reporter_id] = t.unread_count;
    });
    return map;
  }

  window.CaritasChat = {
    openByReporter,
    openByThread,
    listThreads,
    unreadByVillage,
    unreadByReporter,
    onClose: function (fn) {
      window.__ccOnClose = fn;
    },
  };
})();
