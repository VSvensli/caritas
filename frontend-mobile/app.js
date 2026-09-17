// Shared client for the Caritas field-reporter mobile web app.
// Talks to the FastAPI backend, manages the JWT session, and guards pages.

const API = 'http://localhost:8000';

const Session = {
  get access() {
    return localStorage.getItem('access_token');
  },
  get refresh() {
    return localStorage.getItem('refresh_token');
  },
  save(tokens) {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
  },
  clear() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};

// Decode a JWT payload without verifying it (the server verified it on issue).
function decodeToken(jwt) {
  try {
    const part = jwt.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(part));
  } catch {
    return null;
  }
}

function goToLogin() {
  Session.clear();
  window.location.href = 'login.html';
}

// Page guard: ensure a reporter is signed in, else redirect away.
// Staff who land here are sent back to their dashboard. Returns the claims.
function requireReporter() {
  const token = Session.access;
  if (!token) {
    goToLogin();
    return null;
  }
  const claims = decodeToken(token);
  if (!claims) {
    goToLogin();
    return null;
  }
  if (claims.role !== 'reporter') {
    window.location.href = '../frontend-dashboard/dashboard.html';
    return null;
  }
  return claims;
}

// fetch() wrapper that attaches the bearer token and bounces to login on 401.
async function api(path, options = {}) {
  const res = await fetch(API + path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + Session.access,
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) {
    goToLogin();
    throw new Error('Session expired');
  }
  return res;
}

function logout() {
  Session.clear();
  window.location.href = 'login.html';
}

// ── formatting helpers ──────────────────────────────────────────────
const numberFmt = new Intl.NumberFormat('en-US');

function initials(name) {
  return (name || '')
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0] || '')
    .join('')
    .toUpperCase();
}

function firstName(name) {
  return (name || '').trim().split(/\s+/)[0] || '';
}
