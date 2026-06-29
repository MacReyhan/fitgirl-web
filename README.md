# FitGirl Helper — Web Edition 🌐

![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![GitHub Actions](https://img.shields.io/badge/backend-GitHub%20Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)
![GitHub Pages](https://img.shields.io/badge/frontend-GitHub%20Pages-222?style=flat-square&logo=github&logoColor=white)

A **serverless web version** of [FitGirl Helper Redesigned](https://github.com/MacReyhan/fitgirl_helper_redesigned) — no desktop app needed! Runs entirely on GitHub Actions + GitHub Pages.

---

## ✨ Features

- 🌐 **Web-Based UI** — Fluent Design-inspired interface accessible from any browser
- 🤖 **GitHub Actions Backend** — Selenium/Chrome runs on GitHub's servers, not your machine
- 🔒 **Client-Side Credentials** — GitHub PAT stored locally in your browser only
- 🌙 **Dark/Light Theme** — Toggle between themes with one click
- ☑️ **Selective Extraction** — Pick only the files you need
- 📋 **One-Click Copy** — Copy all extracted links to clipboard
- 📱 **Responsive** — Works on mobile, tablet, and desktop

---

## 🚀 Quick Start

### 1. Fork this Repository

Click the **Fork** button at the top of this page.

### 2. Enable GitHub Pages

1. Go to your fork's **Settings → Pages**
2. Set Source to **GitHub Actions** (or deploy from `gh-pages` branch)
3. The site will be available at `https://<your-username>.github.io/<repo-name>/`

### 3. Create a Personal Access Token (PAT)

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a name like `fitgirl-helper-web`
4. Select scopes: **`repo`** and **`workflow`**
5. Generate and copy the token

### 4. Use the Website

1. Open your GitHub Pages URL
2. Paste your PAT, username, and repo name in the setup section
3. Enter a FitGirl repack URL
4. Click **Fetch Links** → select what you want → click **Extract Direct Links**
5. Wait ~2-5 minutes for GitHub Actions to finish
6. Copy your direct download links!

---

## 🏗️ Architecture

```
┌─────────────────────────────┐
│   GitHub Pages (Frontend)   │
│   • Static HTML/CSS/JS      │
│   • Fluent Design UI        │
│   • GitHub API calls         │
└──────────┬──────────────────┘
           │ workflow_dispatch
           ▼
┌─────────────────────────────┐
│   GitHub Actions (Backend)  │
│   • Ubuntu runner           │
│   • Python + Chrome         │
│   • undetected-chromedriver │
│   • Cloudflare bypass       │
└──────────┬──────────────────┘
           │ results JSON → gh-pages
           ▼
┌─────────────────────────────┐
│   GitHub Pages (Results)    │
│   • /results/{id}.json      │
│   • Polled by frontend      │
└─────────────────────────────┘
```

### Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| **Fetch Links** | `fetch-links.yml` | Quick scan: scrapes page for FuckingFast URLs (~1 min) |
| **Extract Links** | `extract-links.yml` | Full extraction: Chrome bypasses Cloudflare (~3-10 min) |
| **Deploy Site** | `deploy-site.yml` | Publishes `docs/` to GitHub Pages |

---

## 📁 Project Structure

```
fitgirl-web/
├── .github/workflows/
│   ├── fetch-links.yml      # Quick scan workflow
│   ├── extract-links.yml    # Full extraction workflow
│   └── deploy-site.yml      # Deploy website to gh-pages
├── docs/
│   └── index.html           # Web frontend (single-page app)
├── scripts/
│   ├── extract.py           # Full extraction script (Selenium)
│   └── fetch_only.py        # Quick fetch script (requests only)
└── README.md
```

---

## ⚠️ Important Notes

- **GitHub Actions minutes**: Free accounts get 2,000 minutes/month. Each extraction uses ~3-10 minutes.
- **Rate limits**: GitHub API has rate limits. Don't spam requests.
- **Privacy**: Your PAT is stored in your browser's `localStorage` — never sent to any server except GitHub's API.
- **Cloudflare changes**: If FuckingFast updates their Cloudflare config, the extraction might need updates.

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Workflow not found" | Make sure the workflow files exist in `.github/workflows/` |
| "Resource not accessible" | Check that your PAT has `repo` + `workflow` scopes |
| Results never appear | Check the Actions tab on GitHub for failed runs |
| Links fail to extract | Cloudflare may have updated; check the extraction logs |

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- Original desktop app: [MacReyhan/fitgirl_helper_redesigned](https://github.com/MacReyhan/fitgirl_helper_redesigned)
- Upstream: [zouhirdev/fitgirl-ff-link-extractor](https://github.com/zouhirdev/fitgirl-ff-link-extractor)
- [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) — Cloudflare bypass
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
