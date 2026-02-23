# 📊 Job Market Intelligence System

A professional desktop application for scraping, sorting, analysing, and visualising job market data from multiple real-world sources — built as a Data Structures & Algorithms project using Python and PyQt6.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 🖥️ Overview

This application demonstrates practical applications of DSA concepts including sorting algorithms, search and filter operations, and data structures — applied to real job market data fetched live from the internet.

**What it does:**
- Fetches hundreds of real jobs from 4 different sources in one click
- Sorts them using 4 classic algorithms with live millisecond timing
- Analyses skill demand, salary distributions, and experience levels
- Displays everything in a professional dark dashboard with interactive charts

---

## ✨ Features

### Job Listings Tab
- One-click fetch from **JSearch (Indeed/LinkedIn)**, **Remotive**, **RemoteOK**, and **Adzuna**
- Pause, Resume, Stop fetch mid-operation with checkpoint recovery
- Click any row to open a **Job Detail panel** — full title, salary, skills, company
- Sort by any column using your chosen algorithm with timing displayed
- Live stat cards — Total Jobs · Remote · Onsite/Hybrid · Salary Coverage
- Source donut chart and posted-date bar chart auto-load after every fetch

### Skill Analyzer Tab
- Top 15 in-demand skills with job count and percentage coverage
- Colour-gradient horizontal bar chart (darker → brighter by rank)
- Auto-refreshes after every fetch

### Salary & Experience Tab
- Hero stat cards — Average, Min, Max salary and jobs-with-salary count
- Salary histogram bucketed by $20k ranges with coverage subtitle
- Experience distribution shown as pie + bar chart side by side

### Filter & Export Tab
- Results update **live as you type** — no Apply button needed
- Filter by role, location, salary range, and experience level
- Filtered salary preview chart updates in real time
- Export as **CSV** or **JSON**

### Performance Analytics Tab *(DSA focus)*
- Compare any two sorting algorithms head-to-head on current data
- **Benchmark ALL 4** in one click — ranked chart with winner highlighted
- Sort time timeline across last 30 runs, colour-coded by algorithm
- Full history table: algorithm · column · time (ms) · job count

---

## 🔢 Sorting Algorithms Implemented

| Algorithm | Best Case | Average | Worst Case | Stable |
|---|---|---|---|---|
| **Quick Sort** | O(n log n) | O(n log n) | O(n²) | No |
| **Merge Sort** | O(n log n) | O(n log n) | O(n log n) | Yes |
| **Bubble Sort** | O(n) | O(n²) | O(n²) | Yes |
| **Tim Sort** | O(n) | O(n log n) | O(n log n) | Yes |

Each sort is timed to the millisecond and logged to `data/sort_history.json`.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| GUI Framework | PyQt6 |
| Charts | Matplotlib |
| Database | SQLite (Python built-in) |
| HTTP Requests | `requests` |
| Skill Extraction | Custom NLP module |
| Language | Python 3.11+ |

---

## 📁 Project Structure

```
job-market-intelligence/
│
├── main.py                        # Entry point
├── requirements.txt
├── README.md
│
├── config/
│   └── constants.py               # APP_NAME, SALARY_CURRENCY, etc.
│
├── database/
│   └── db_manager.py              # SQLite manager with deduplication
│
├── ui/
│   ├── main_window.py             # All 5 tabs — complete dashboard
│   ├── workers.py                 # UnifiedFetchWorker (QThread)
│   ├── chart_widget.py            # ChartCanvas with fullscreen support
│   └── styles.py                  # Full dark stylesheet
│
├── sorting/
│   └── sorting_algorithms.py      # All 4 algorithms + timer
│
├── analysis/
│   ├── filter_search.py           # Multi-field job filter
│   ├── skill_analyzer.py          # top_skills() NLP-based
│   ├── salary_experience.py       # Salary + experience aggregation
│   ├── export_reports.py          # CSV export
│   ├── performance_tracker.py     # Sort history and averages
│   ├── salary_normalizer.py       # Multi-currency → USD normalisation
│   └── skills_extractor.py        # Skills from title + description
│
└── data/                          # Auto-created at runtime
    ├── jobs.db                    # SQLite database
    ├── sort_history.json          # Algorithm performance log
    └── state.json                 # Pause/resume checkpoint
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/javairia772/job-market-intelligence.git
cd job-market-intelligence
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run

```bash
python main.py
```

---

## 🔑 API Keys Setup

Two sources work immediately with no setup. Two optional sources require free API keys.

### No key needed ✅

| Source | Type |
|---|---|
| **Remotive** | Remote tech jobs |
| **RemoteOK** | Remote jobs (high volume) |

---

### JSearch — Indeed · LinkedIn · Glassdoor

JSearch is a RapidAPI service that provides structured job data aggregated from Indeed, LinkedIn and Glassdoor through a legitimate API. This replaces direct Indeed HTML scraping which is blocked with a 403 error.

**Free tier: 200 requests / month**

**Get your key:**
1. Go to [rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
2. Click **Subscribe to Test** → select the **Free** plan
3. Copy your `X-RapidAPI-Key` from the right-hand code panel

**Set the key:**

```powershell
# Windows — current session
$env:JSEARCH_API_KEY = "your_key_here"
python main.py
```

```bash
# macOS / Linux — current session
export JSEARCH_API_KEY="your_key_here"
python main.py
```

**Windows — permanent:**
1. Start → search **"Edit the system environment variables"**
2. Click **Environment Variables**
3. Under User Variables → **New**
4. Name: `JSEARCH_API_KEY` · Value: your key
5. Restart terminal

---

### Adzuna — Onsite & Hybrid Jobs

**Free tier available**

1. Go to [developer.adzuna.com](https://developer.adzuna.com)
2. Sign up → Create an application → copy your **App ID** and **App Key**

```powershell
# Windows — current session
$env:ADZUNA_APP_ID  = "your_app_id"
$env:ADZUNA_APP_KEY = "your_app_key"
python main.py
```

```bash
# macOS / Linux — current session
export ADZUNA_APP_ID="your_app_id"
export ADZUNA_APP_KEY="your_app_key"
python main.py
```

> If API keys are not set, those sources are skipped silently — Remotive and RemoteOK still load fine.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+R` | Fetch all sources |
| `Ctrl+F` | Jump to Filter tab |
| `Ctrl+E` | Export current filtered data |

---

## 📝 .gitignore

Add this file to your project root before pushing:

```gitignore
# Virtual environment
venv/
.venv/

# Python cache
__pycache__/
*.pyc
*.pyo

# Runtime data — generated by the app, do not commit
data/
*.db
sort_history.json
state.json

# API keys and secrets — NEVER commit these
.env
*.env

# IDE
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
```


---

## 👨‍💻 About

**BS Computer Science — Semester 3**
Data Structures & Algorithms — Semester Project

This project applies core DSA concepts to a real-world problem:
- **Sorting** — 4 algorithms benchmarked on live job data
- **Search & Filter** — multi-field linear scan with live results
- **Hash-based deduplication** — SQLite unique constraints prevent duplicate jobs
- **Data aggregation** — grouping and counting for skill/salary analysis

---

## 📄 License

MIT License — free to use, modify, and distribute with attribution.