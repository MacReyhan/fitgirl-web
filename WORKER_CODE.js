// ╔══════════════════════════════════════════════════════════════════╗
// ║  FitGirl Helper — Cloudflare Worker                             ║
// ║  Copy ALL of this code and paste it into Cloudflare Worker      ║
// ║                                                                  ║
// ║  Required Secrets (add in Settings → Variables):                ║
// ║    GITHUB_TOKEN  = ghp_xxxxx  (repo + workflow scopes)          ║
// ║    GITHUB_OWNER  = YourUsername                                  ║
// ║    GITHUB_REPO   = your-repo-name                               ║
// ╚══════════════════════════════════════════════════════════════════╝

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS')
      return new Response(null, { status: 204, headers: CORS });

    const url = new URL(request.url);
    const path = url.pathname;

    try {
      if (request.method === 'POST' && path === '/fetch')
        return await handleFetch(request);

      if (request.method === 'POST' && path === '/extract')
        return await handleExtract(request, env);

      if (request.method === 'GET' && path.startsWith('/status/'))
        return await handleStatus(path.split('/status/')[1], env);

      return json({ error: 'Not found' }, 404);
    } catch (err) {
      return json({ error: err.message }, 500);
    }
  }
};

// ── POST /fetch ── Scrape FitGirl page for FuckingFast links (instant) ──
async function handleFetch(request) {
  const body = await request.json();
  const pageUrl = body.url;
  if (!pageUrl) return json({ error: 'Missing url' }, 400);

  const resp = await fetch(pageUrl, {
    headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' },
  });
  if (!resp.ok) return json({ error: `Page returned HTTP ${resp.status}` }, 502);

  const html = await resp.text();

  // Extract FF links
  const regex = /href="(https?:\/\/[^"]*fuckingfast\.co[^"]*)"/gi;
  const links = [];
  const seen = new Set();
  let m;
  while ((m = regex.exec(html)) !== null) {
    if (!seen.has(m[1])) {
      seen.add(m[1]);
      const fn = m[1].includes('#') ? m[1].split('#').pop() : m[1].split('/').pop();
      links.push({ url: m[1], filename: decodeURIComponent(fn) });
    }
  }

  // Extract title
  const titleMatch = html.match(/<h1[^>]*class="entry-title"[^>]*>(.*?)<\/h1>/i);
  const title = titleMatch ? titleMatch[1].replace(/<[^>]+>/g, '').trim() : null;

  return json({ status: 'ok', game_title: title, count: links.length, links });
}

// ── POST /extract ── Trigger GitHub Actions workflow ────────────────────
async function handleExtract(request, env) {
  const body = await request.json();
  if (!body.url) return json({ error: 'Missing url' }, 400);
  if (!env.GITHUB_TOKEN || !env.GITHUB_OWNER || !env.GITHUB_REPO)
    return json({ error: 'Server not configured — add GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO as Worker secrets' }, 500);

  const requestId = body.request_id || ('r_' + Date.now().toString(36));

  const ghResp = await fetch(
    `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/extract-links.yml/dispatches`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'FitGirl-Worker',
      },
      body: JSON.stringify({
        ref: 'main',
        inputs: {
          fitgirl_url: body.url,
          request_id: requestId,
          selected_indices: body.selected_indices || '',
        },
      }),
    }
  );

  if (!ghResp.ok) {
    const t = await ghResp.text();
    return json({ error: `GitHub ${ghResp.status}: ${t}` }, 502);
  }

  return json({ status: 'triggered', request_id: requestId });
}

// ── GET /status/:id ── Poll for extraction results ──────────────────────
async function handleStatus(requestId, env) {
  if (!env.GITHUB_TOKEN || !env.GITHUB_OWNER || !env.GITHUB_REPO)
    return json({ error: 'Server not configured' }, 500);

  // Try reading result from gh-pages
  const rawResp = await fetch(
    `https://raw.githubusercontent.com/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/gh-pages/results/${requestId}.json`,
    { headers: { 'Authorization': `Bearer ${env.GITHUB_TOKEN}`, 'User-Agent': 'FitGirl-Worker' } }
  );

  if (rawResp.ok) {
    const data = await rawResp.json();
    return json({ status: 'ready', data });
  }

  // Check workflow status
  let ws = 'queued';
  try {
    const runsResp = await fetch(
      `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/runs?per_page=3`,
      { headers: { 'Authorization': `Bearer ${env.GITHUB_TOKEN}`, 'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'FitGirl-Worker' } }
    );
    if (runsResp.ok) {
      const runs = await runsResp.json();
      const r = runs.workflow_runs?.[0];
      if (r) ws = r.conclusion ? `${r.status} (${r.conclusion})` : r.status;
    }
  } catch(e) {}

  return json({ status: 'pending', workflow_status: ws });
}

// Helper
function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  });
}
