/**
 * FitGirl Helper — Cloudflare Worker Backend
 *
 * Handles two endpoints:
 *   POST /fetch   → Scrapes a FitGirl page for FuckingFast links (instant)
 *   POST /extract → Triggers GitHub Actions for Selenium extraction (async)
 *   GET  /status/:id → Checks extraction result from GitHub Actions
 *
 * Environment variables (set in Cloudflare dashboard as Secrets):
 *   GITHUB_TOKEN  → GitHub PAT with repo + workflow scopes
 *   GITHUB_OWNER  → GitHub username (e.g. "MacReyhan")
 *   GITHUB_REPO   → Repository name (e.g. "fitgirl_helper_web")
 *   API_SECRET    → Optional: shared secret to protect your Worker from abuse
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, X-Api-Key',
};

export default {
  async fetch(request, env) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    const path = url.pathname;

    try {
      // Optional: check API secret
      if (env.API_SECRET) {
        const key = request.headers.get('X-Api-Key') || url.searchParams.get('key');
        if (key !== env.API_SECRET) {
          return jsonResponse({ error: 'Unauthorized' }, 403);
        }
      }

      if (request.method === 'POST' && path === '/fetch') {
        return await handleFetch(request, env);
      }

      if (request.method === 'POST' && path === '/extract') {
        return await handleExtract(request, env);
      }

      if (request.method === 'GET' && path.startsWith('/status/')) {
        const requestId = path.split('/status/')[1];
        return await handleStatus(requestId, env);
      }

      return jsonResponse({ error: 'Not found', endpoints: ['/fetch', '/extract', '/status/:id'] }, 404);

    } catch (err) {
      return jsonResponse({ error: err.message || 'Internal server error' }, 500);
    }
  }
};

// ── /fetch — Scrape FitGirl page for FuckingFast links ──────────────────
async function handleFetch(request, env) {
  const body = await request.json();
  const fitgirlUrl = body.url;

  if (!fitgirlUrl || !fitgirlUrl.includes('fitgirl')) {
    return jsonResponse({ error: 'Invalid or missing FitGirl URL' }, 400);
  }

  // Fetch the page
  const resp = await fetch(fitgirlUrl, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    },
  });

  if (!resp.ok) {
    return jsonResponse({ error: `Failed to fetch page: HTTP ${resp.status}` }, 502);
  }

  const html = await resp.text();

  // Parse FuckingFast links
  const linkRegex = /href="(https?:\/\/[^"]*fuckingfast\.co[^"]*)"/gi;
  const links = [];
  const seen = new Set();
  let match;

  while ((match = linkRegex.exec(html)) !== null) {
    const href = match[1];
    if (!seen.has(href)) {
      seen.add(href);
      const filename = href.includes('#') ? href.split('#').pop() : href.split('/').pop();
      links.push({ url: href, filename: decodeURIComponent(filename) });
    }
  }

  // Extract game title
  const titleMatch = html.match(/<h1[^>]*class="entry-title"[^>]*>(.*?)<\/h1>/i);
  const gameTitle = titleMatch ? titleMatch[1].replace(/<[^>]+>/g, '').trim() : null;

  return jsonResponse({
    status: 'ok',
    game_title: gameTitle,
    count: links.length,
    links: links,
  });
}

// ── /extract — Trigger GitHub Actions workflow ──────────────────────────
async function handleExtract(request, env) {
  const body = await request.json();
  const fitgirlUrl = body.url;
  const selectedIndices = body.selected_indices || '';
  const requestId = body.request_id || generateId();

  if (!fitgirlUrl) {
    return jsonResponse({ error: 'Missing URL' }, 400);
  }

  if (!env.GITHUB_TOKEN || !env.GITHUB_OWNER || !env.GITHUB_REPO) {
    return jsonResponse({ error: 'Server misconfigured: missing GitHub credentials' }, 500);
  }

  // Trigger workflow_dispatch
  const ghUrl = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/extract-links.yml/dispatches`;

  const ghResp = await fetch(ghUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
      'User-Agent': 'FitGirl-Helper-Worker',
    },
    body: JSON.stringify({
      ref: 'main',
      inputs: {
        fitgirl_url: fitgirlUrl,
        request_id: requestId,
        selected_indices: selectedIndices,
      },
    }),
  });

  if (!ghResp.ok) {
    const errText = await ghResp.text();
    return jsonResponse({ error: `GitHub API error: ${ghResp.status} — ${errText}` }, 502);
  }

  return jsonResponse({
    status: 'triggered',
    request_id: requestId,
    message: 'Extraction workflow started. Poll /status/' + requestId + ' for results.',
  });
}

// ── /status/:id — Check if extraction results are ready ─────────────────
async function handleStatus(requestId, env) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_OWNER || !env.GITHUB_REPO) {
    return jsonResponse({ error: 'Server misconfigured' }, 500);
  }

  // Try to read the result file from gh-pages (committed by the workflow)
  const rawUrl = `https://raw.githubusercontent.com/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/gh-pages/results/${requestId}.json`;

  const resp = await fetch(rawUrl, {
    headers: {
      'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3.raw',
      'User-Agent': 'FitGirl-Helper-Worker',
    },
  });

  if (resp.ok) {
    const data = await resp.json();
    return jsonResponse({ status: 'ready', data });
  }

  // Not ready yet — check workflow run status
  const runsUrl = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/runs?per_page=5&event=workflow_dispatch`;
  const runsResp = await fetch(runsUrl, {
    headers: {
      'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'FitGirl-Helper-Worker',
    },
  });

  let workflowStatus = 'unknown';
  if (runsResp.ok) {
    const runsData = await runsResp.json();
    const latestRun = runsData.workflow_runs?.[0];
    if (latestRun) {
      workflowStatus = latestRun.status;
      if (latestRun.conclusion) workflowStatus += ` (${latestRun.conclusion})`;
    }
  }

  return jsonResponse({
    status: 'pending',
    workflow_status: workflowStatus,
    message: 'Results not ready yet. Keep polling.',
  });
}

// ── Helpers ──────────────────────────────────────────────────────────────
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...CORS_HEADERS,
    },
  });
}

function generateId() {
  return 'req_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
}
