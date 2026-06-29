# 🔗 FitGirl Helper Web

A serverless, automated web tool to scrape and extract direct download links from FitGirl repack pages, bypassing Cloudflare verification on hosters like **FuckingFast.co**. 

It combines a responsive, premium web interface with a Cloudflare Worker backend API and a GitHub Actions workflow running Selenium to resolve direct download links on demand.

---

## 📖 What is this Website About?

When downloading repacks from FitGirl, files are often split into multiple parts and hosted on platforms like **FuckingFast**. Manually clicking through dozens of links, solving Cloudflare CAPTCHAs, and copying direct download links is tedious and time-consuming.

**FitGirl Helper Web** automates this entire process:
1. **Scrape**: Paste a FitGirl page URL. The backend instantly scans the page and returns a checklist of all available parts.
2. **Select**: Choose the specific parts you want to download (e.g., skip optional languages or selective files).
3. **Resolve**: Trigger the extraction. A headless Chrome instance (`undetected-chromedriver`) is launched via GitHub Actions to automatically bypass Cloudflare on the hosting pages and capture the direct download links.
4. **Download**: View, copy, or open all direct download URLs simultaneously.

---

## ✨ Features

- ⚡ **Instant Scraper**: Fast parsing of FitGirl pages to retrieve titles and file paths.
- 🎯 **Selective Parts**: Extract only what you need, minimizing compute time and bandwidth.
- 🛡️ **Cloudflare Bypass**: Utilizes headless Chrome to bypass Cloudflare wait screens dynamically.
- ☁️ **Fully Serverless & Free**: Runs entirely on the free tiers of Cloudflare Workers, GitHub Actions, and GitHub Pages.
- 🎨 **Responsive UI**: A premium dark-themed dashboard with status trackers, copy-to-clipboard buttons, and toast notifications.

---

## 🛠️ Architecture & Tech Stack

This project is built using a serverless decoupling strategy:

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JS | A single-page dashboard for user interactions, hosted on GitHub Pages. |
| **Backend API** | Cloudflare Workers | Serverless edge handlers that scrape FitGirl pages and trigger GitHub workflows. |
| **Resolver Script** | Python 3.11, Selenium | Python scraper running `undetected-chromedriver` to execute browser-level interactions. |
| **Runner** | GitHub Actions | Automates the headless Chrome runner, publishing results back via the `gh-pages` branch. |

---

## 📁 Repository Structure

- [**`site/index.html`**](file:///c:/Users/mbgaming/Downloads/Compressed/fitgirl-web/site/index.html) — The frontend web application.
- [**`scripts/extract.py`**](file:///c:/Users/mbgaming/Downloads/Compressed/fitgirl-web/scripts/extract.py) — Python browser-automation script that resolves FuckingFast links.
- [**`.github/workflows/extract-links.yml`**](file:///c:/Users/mbgaming/Downloads/Compressed/fitgirl-web/.github/workflows/extract-links.yml) — GitHub Actions runner configuration.
- [**`WORKER_CODE.js`**](file:///c:/Users/mbgaming/Downloads/Compressed/fitgirl-web/WORKER_CODE.js) — Cloudflare Worker script handling the APIs.
- [**`DEPLOY_GUIDE.html`**](file:///c:/Users/mbgaming/Downloads/Compressed/fitgirl-web/DEPLOY_GUIDE.html) — An interactive, step-by-step local deployment guide.

---

## 🚀 Setup & Deployment

For a full interactive walkthrough on setting up your own instance, open and view [**`DEPLOY_GUIDE.html`**](file:///c:/Users/mbgaming/Downloads/Compressed/fitgirl-web/DEPLOY_GUIDE.html) in your browser.

### Quick Setup Overview:
1. **Fork the Repo**: Fork this repository to your own GitHub account.
2. **GitHub PAT**: Generate a Personal Access Token with `repo` and `workflow` scopes.
3. **Deploy Worker**:
   - Create a Cloudflare Worker and paste the code from [**`WORKER_CODE.js`**](file:///c:/Users/mbgaming/Downloads/Compressed/fitgirl-web/WORKER_CODE.js).
   - Configure secrets in Cloudflare dashboard settings: `GITHUB_TOKEN`, `GITHUB_OWNER`, and `GITHUB_REPO`.
4. **Configure Site**:
   - Edit [**`site/index.html`**](file:///c:/Users/mbgaming/Downloads/Compressed/fitgirl-web/site/index.html) and replace `%%WORKER_URL%%` with your actual Cloudflare Worker domain endpoint (e.g., `https://your-worker.workers.dev`).
5. **Enable GitHub Pages**:
   - In your repository settings, set up GitHub Pages to deploy from the `/site` directory of the `main` branch.

---

## 🤝 Credits & Acknowledgements

This application was made possible thanks to the following creators and open-source projects:

- **Developer**: Created by [MacReyhan](https://github.com/MacReyhan)
- **Selenium Undetected Chromedriver**: [ultrafunkamsterdam/undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver) — for making browser-based scraping of Cloudflare-protected pages possible.
- **BeautifulSoup**: [BS4](https://www.crummy.com/software/BeautifulSoup/) — for pythonic HTML parsing.
- **Workers**: Hosted and proxied via [Cloudflare Workers](https://workers.cloudflare.com/).

---

## ⚠️ Disclaimer

This tool is created for educational purposes and personal utility. Please respect the terms of service of the websites you interact with. The author is not responsible for any misuse of this tool.
