# Job Market Intelligence System

A desktop application for aggregating, analyzing, and exporting job market data. Built with **Python**, **PyQt6**, **SQLite**, and **DSA** (sorting algorithms). Suitable as a portfolio project demonstrating full-stack desktop development, data pipelines, and algorithm implementation.

---

## Features

- **Multi-source job data**
  - **Fetch All** – load 500+ jobs from Remotive + [RemoteOK](https://remoteok.com/api) in one click
  - **Remotive** – ~50 jobs from [Remotive API](https://remotive.com/api/remote-jobs)
  - **Indeed** – scrape by role and location (onsite, hybrid, remote)
- **Adzuna** – fetch onsite/hybrid jobs (optional; set `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`; [free signup](https://developer.adzuna.com/signup))
- **Replace vs Append** – choose whether new data replaces or appends to existing jobs
- **Sorting** – sort by any column using **Quick Sort**, **Merge Sort**, **Bubble Sort**, or **Tim Sort**, with execution time displayed
- **Skill analysis** – top N skills across listings with bar chart (matplotlib)
- **Salary & experience** – average salary by role and experience distribution with charts
- **Filter & export** – filter by role, location, salary range, experience; **export filtered results to CSV** with save dialog
- **Status bar** – total job count; progress feedback during fetch/scrape
- **Error handling** – user-friendly messages for network/API failures and empty data

**Note:** Data is **not** fetched automatically on a schedule. You get fresh data when you click **Fetch Remotive** or **Scrape Indeed**. For “live” data, run the app and use those buttons whenever you want an update.

---

## Tech Stack

| Layer        | Technology                          |
|-------------|--------------------------------------|
| UI          | PyQt6 (Qt for Python)               |
| Database    | SQLite (via `sqlite3`)              |
| Data sources| Indeed (BeautifulSoup), Remotive API|
| Analysis    | Collections, regex, matplotlib     |
| Algorithms  | Custom Quick/Merge/Bubble + built-in Tim sort |

---

## Setup

### Prerequisites

- Python 3.9+
- pip

### Install

```bash
# Clone or download the project, then:
cd "Job Market Intelligence System"   # or your project folder
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

Run from the **project root** (where `main.py` lives) so the app finds the `data/` folder for the SQLite database.

---

## Project Structure

```
├── main.py              # Entry point
├── requirements.txt
├── README.md
├── config/
│   ├── __init__.py
│   └── constants.py    # App name, column indices, project root
├── database/
│   └── db_manager.py   # SQLite schema and CRUD
├── ui/
│   ├── main_window.py  # Tabs, tables, and event handlers
│   ├── workers.py      # QThread workers for scrape/fetch
│   ├── chart_widget.py # Embedded matplotlib charts
│   └── styles.py       # Modern dark theme stylesheet
├── scraper/
│   ├── indeed_scraper.py   # Indeed scraping (optional append)
│   ├── remotive_api.py     # Remotive API client
│   ├── remoteok_api.py     # RemoteOK API (500+ jobs)
│   └── adzuna_api.py       # Adzuna API (onsite/hybrid; requires API key)
├── sorting/
│   └── sorting_algorithms.py  # Quick, Merge, Bubble, Tim sort
├── analysis/
│   ├── filter_search.py
│   ├── skill_analyzer.py
│   ├── salary_experience.py  # Stats + chart figures (skills, salary, experience)
│   └── export_reports.py
└── data/               # Created at runtime
    └── jobs.db
```

---

## Usage Tips

1. **First run** – Use **Fetch All Remote Jobs** for 500+ jobs instantly. **Scrape Indeed** may be rate-limited.
2. **Indeed** – May be rate-limited or blocked; use sparingly. Prefer Remotive for reliable remote jobs.
3. **Export** – Apply filters in the **Filter & Export** tab, then click **Export to CSV...** and choose a path.
4. **Salary** – Shown in **USD** where available; otherwise «Not specified». Adzuna (country `gb`) may show GBP.
5. **Adzuna (onsite/hybrid)** – Set `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` in your environment, then restart the app to enable the button.

---

## License

Use for learning and portfolio. Respect Remotive’s [API terms](https://remotive.com/api-documentation) and Indeed’s robots.txt when scraping.
