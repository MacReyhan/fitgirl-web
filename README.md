# FitGirl Helper — Web Edition 🌐

A **serverless web version** of FitGirl Helper. No desktop app, no installs. Everything runs on **Cloudflare Workers** + **GitHub Actions**.

Users see a clean website — **zero configuration needed** on their end. All secrets stay on the server.

---

## 🏗️ Architecture

```
User's Browser              Cloudflare Worker              GitHub Actions
┌──────────┐   /fetch    ┌────────────────────┐
│  Website  │───────────▶│  Scrapes FitGirl   │  (instant, ~1s)
│           │◀───────────│  Returns links     │
│           │            └────────────────────┘
│           │   /extract ┌────────────────────┐  workflow_dispatch  ┌─────────────┐
│           │───────────▶│  Triggers GitHub   │───────────────────▶│ Chrome runs  │
│           │            │  Actions workflow  │                    │ Bypasses CF  │
│           │            └────────────────────┘                    │ Saves result │
│           │   /status  ┌────────────────────┐  reads gh-pages    └──────┬──────┘
│           │───────────▶│  Checks for result │◀──────────────────────────┘
│           │◀───────────│  Returns links     │
└──────────┘            └────────────────────┘
```

---

## 🚀 Setup (One-Time, ~10 minutes)

### Step 1 — Fork/Clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/fitgirl_helper_web.git
cd fitgirl_helper_web
```

Push it to your own GitHub repository.

### Step 2 — Create a GitHub Personal Access Token

1. Go to **[github.com/settings/tokens](https://github.com/settings/tokens)**
2. **Generate new token (classic)**
3. Name: `fitgirl-worker`
4. Scopes: ✅ `repo`, ✅ `workflow`
5. Copy the token (starts with `ghp_...`)

### Step 3 — Deploy the Cloudflare Worker

**Option A: Cloudflare Dashboard (easiest)**

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create**
2. Click **"Create Worker"**
3. Name it `fitgirl-helper-api` → **Deploy**
4. Click **"Edit Code"** → paste the contents of `worker/worker.js` → **Deploy**
5. Go to **Settings → Variables and Secrets** and add:

   | Variable | Type | Value |
   |----------|------|-------|
   | `GITHUB_TOKEN` | **Secret** | Your PAT from Step 2 |
   | `GITHUB_OWNER` | Text | Your GitHub username |
   | `GITHUB_REPO` | Text | Your repo name |
   | `API_SECRET` | **Secret** | *(optional)* A random string to protect your API |

6. Note your Worker URL: `https://fitgirl-helper-api.YOUR_SUBDOMAIN.workers.dev`

**Option B: Wrangler CLI**

```bash
cd worker
npm install -g wrangler
wrangler login
wrangler secret put GITHUB_TOKEN    # paste your PAT
wrangler secret put API_SECRET      # optional
wrangler deploy
```

Then add `GITHUB_OWNER` and `GITHUB_REPO` as plain text vars in the dashboard or `wrangler.toml`.

### Step 4 — Set the Worker URL in the website

Open `site/index.html` and replace `%%WORKER_URL%%` with your actual Worker URL:

```js
const API_URL = 'https://fitgirl-helper-api.your-subdomain.workers.dev';
```

### Step 5 — Deploy the website to Cloudflare Pages

1. Go to Cloudflare Dashboard → **Workers & Pages** → **Create** → **Pages**
2. Connect your GitHub repo
3. Build settings:
   - **Build command:** *(leave empty)*
   - **Build output directory:** `site`
4. **Deploy!**

Your site is now live at `https://your-project.pages.dev` 🎉

### Step 6 — Enable gh-pages branch

The extraction workflow saves results to the `gh-pages` branch. Create it:

```bash
git checkout --orphan gh-pages
git rm -rf .
echo "results" > .gitignore
mkdir results
touch results/.gitkeep
git add .
git commit -m "init gh-pages"
git push origin gh-pages
git checkout main
```

---

## ✅ That's it!

Users visit your site → paste a URL → click Fetch → select parts → click Extract → get direct links.

**They never see or touch any tokens, API keys, or configuration.**

---

## 🔒 Security

| Concern | Answer |
|---------|--------|
| Where is the GitHub token? | Stored as an **encrypted secret** in Cloudflare Worker environment variables. Never exposed to the browser. |
| Can someone abuse the Worker? | Set `API_SECRET` and add `?key=YOUR_SECRET` to the frontend `API_URL`, or implement rate limiting. |
| What about CORS? | The Worker includes permissive CORS headers. Lock it down to your domain if needed. |

---

## 💰 Cost

| Service | Free Tier |
|---------|-----------|
| Cloudflare Workers | 100,000 requests/day |
| Cloudflare Pages | Unlimited static hosting |
| GitHub Actions | 2,000 minutes/month (free tier) |

Each extraction uses ~3-10 minutes of Actions time. You can run **200-600 extractions/month** for free.

---

## 📁 File Structure

```
├── .github/workflows/
│   └── extract-links.yml    # GitHub Actions extraction workflow
├── worker/
│   ├── worker.js            # Cloudflare Worker (API backend)
│   └── wrangler.toml        # Wrangler configuration
├── scripts/
│   └── extract.py           # Python extraction script (runs in Actions)
├── site/
│   └── index.html           # Frontend website
└── README.md
```

---

## 🔧 Optional: Protect the API

If you set `API_SECRET` in your Worker, update the frontend:

```js
const API_URL = 'https://fitgirl-helper-api.your-sub.workers.dev?key=YOUR_SECRET';
```

Or better yet, add the key as a header in the `api()` function.

---

## 📝 License

MIT
