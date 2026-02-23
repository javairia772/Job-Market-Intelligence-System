"""
Skills Extractor
================
Scans job title + description text for known tech / domain skills.
Used to enrich Adzuna and Indeed jobs that return "Not specified" skills.

Usage
-----
    from analysis.skills_extractor import extract_skills_from_text

    skills_str = extract_skills_from_text(title + " " + description)
    # → "Python, SQL, AWS"   or   "Not specified"
"""

import re

# ── Master skill keyword list ─────────────────────────────────────────────────
# Organised by category for readability; all lowercased for matching.
_SKILL_KEYWORDS: list[tuple[str, str]] = [
    # Languages
    ("python",        "Python"),
    ("javascript",    "JavaScript"),
    ("typescript",    "TypeScript"),
    ("java",          "Java"),
    ("kotlin",        "Kotlin"),
    ("swift",         "Swift"),
    ("c#",            "C#"),
    ("c\\+\\+",       "C++"),
    ("golang",        "Go"),
    (r"\bgo\b",       "Go"),
    ("rust",          "Rust"),
    ("ruby",          "Ruby"),
    ("php",           "PHP"),
    ("scala",         "Scala"),
    ("r\\b",          "R"),
    ("dart",          "Dart"),
    ("bash",          "Bash"),
    ("shell",         "Shell"),
    ("perl",          "Perl"),

    # Web / Frontend
    ("react",         "React"),
    ("vue",           "Vue.js"),
    ("angular",       "Angular"),
    ("next\\.?js",    "Next.js"),
    ("svelte",        "Svelte"),
    ("html",          "HTML"),
    ("css",           "CSS"),
    ("tailwind",      "Tailwind"),
    ("bootstrap",     "Bootstrap"),
    ("jquery",        "jQuery"),
    ("graphql",       "GraphQL"),
    ("rest api",      "REST API"),
    ("webpack",       "Webpack"),

    # Backend / Frameworks
    ("django",        "Django"),
    ("flask",         "Flask"),
    ("fastapi",       "FastAPI"),
    ("spring",        "Spring"),
    ("node\\.?js",    "Node.js"),
    ("express",       "Express"),
    ("rails",         "Ruby on Rails"),
    ("laravel",       "Laravel"),
    ("asp\\.net",     "ASP.NET"),
    ("\\.net",        ".NET"),

    # Databases
    ("postgresql",    "PostgreSQL"),
    ("postgres",      "PostgreSQL"),
    ("mysql",         "MySQL"),
    ("sqlite",        "SQLite"),
    ("mongodb",       "MongoDB"),
    ("redis",         "Redis"),
    ("elasticsearch", "Elasticsearch"),
    ("cassandra",     "Cassandra"),
    ("dynamodb",      "DynamoDB"),
    ("snowflake",     "Snowflake"),
    ("bigquery",      "BigQuery"),
    (r"\bsql\b",      "SQL"),

    # Cloud / DevOps
    ("aws",           "AWS"),
    ("azure",         "Azure"),
    ("gcp",           "GCP"),
    ("google cloud",  "GCP"),
    ("docker",        "Docker"),
    ("kubernetes",    "Kubernetes"),
    (r"\bk8s\b",      "Kubernetes"),
    ("terraform",     "Terraform"),
    ("ansible",       "Ansible"),
    ("jenkins",       "Jenkins"),
    ("github actions","GitHub Actions"),
    ("circleci",      "CircleCI"),
    ("ci/cd",         "CI/CD"),
    ("linux",         "Linux"),
    ("nginx",         "Nginx"),

    # Data / ML / AI
    ("machine learning","Machine Learning"),
    (r"\bml\b",        "Machine Learning"),
    ("deep learning",  "Deep Learning"),
    ("tensorflow",     "TensorFlow"),
    ("pytorch",        "PyTorch"),
    ("scikit.learn",   "Scikit-learn"),
    ("pandas",         "Pandas"),
    ("numpy",          "NumPy"),
    ("spark",          "Apache Spark"),
    ("hadoop",         "Hadoop"),
    ("airflow",        "Airflow"),
    ("dbt",            "dbt"),
    ("tableau",        "Tableau"),
    ("power bi",       "Power BI"),
    ("looker",         "Looker"),
    ("nlp",            "NLP"),
    ("llm",            "LLM"),
    ("langchain",      "LangChain"),
    ("openai",         "OpenAI"),

    # Mobile
    ("android",       "Android"),
    ("ios",           "iOS"),
    ("flutter",       "Flutter"),
    ("react native",  "React Native"),
    ("xamarin",       "Xamarin"),

    # Security
    ("cybersecurity", "Cybersecurity"),
    ("penetration",   "Pen Testing"),
    ("owasp",         "OWASP"),
    ("siem",          "SIEM"),
    ("soc",           "SOC"),

    # Tools / Practices
    ("git",           "Git"),
    ("jira",          "Jira"),
    ("agile",         "Agile"),
    ("scrum",         "Scrum"),
    ("microservices", "Microservices"),
    ("api",           "API"),
    ("kafka",         "Kafka"),
    ("rabbitmq",      "RabbitMQ"),
    ("prometheus",    "Prometheus"),
    ("grafana",       "Grafana"),

    # Domains
    ("blockchain",    "Blockchain"),
    ("solidity",      "Solidity"),
    ("web3",          "Web3"),
    ("devops",        "DevOps"),
    ("devsecops",     "DevSecOps"),
    ("sre",           "SRE"),
]

# Pre-compile patterns for speed
_COMPILED: list[tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), label)
    for pattern, label in _SKILL_KEYWORDS
]


def extract_skills_from_text(text: str, max_skills: int = 15) -> str:
    """
    Scan `text` (title + description) for known skills.

    Returns
    -------
    str
        Comma-separated skill names, e.g. "Python, Django, PostgreSQL, AWS"
        Returns "Not specified" if nothing found.
    """
    if not text or not text.strip():
        return "Not specified"

    found: list[str] = []
    seen: set[str] = set()

    for pattern, label in _COMPILED:
        if label in seen:
            continue
        if pattern.search(text):
            found.append(label)
            seen.add(label)
        if len(found) >= max_skills:
            break

    return ", ".join(found) if found else "Not specified"


def enrich_skills(title: str, description: str, existing_skills: str) -> str:
    """
    Use existing skills if present; otherwise extract from title + description.
    Call this in every scraper pipeline before inserting into the DB.

    Parameters
    ----------
    title : str
        Job title.
    description : str
        Full or partial job description text.
    existing_skills : str
        Skills string already produced by the scraper (may be "Not specified").

    Returns
    -------
    str
        Best available skills string.
    """
    if (
        existing_skills
        and existing_skills.strip()
        and existing_skills.strip().lower() not in ("not specified", "n/a", "none", "")
    ):
        return existing_skills   # already good — keep it

    return extract_skills_from_text(f"{title} {description}")


# ── quick self-test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("Senior Python Developer",
         "We use Django, PostgreSQL, Docker and AWS. CI/CD with GitHub Actions.",
         "Python, Django, PostgreSQL, Docker, AWS, CI/CD, GitHub Actions"),

        ("Data Analyst – Power BI & SQL",
         "Experience with BigQuery, Tableau, or Looker preferred. Pandas a plus.",
         "SQL, Power BI, BigQuery, Tableau, Looker, Pandas"),

        ("iOS Engineer",
         "Swift development for our mobile apps. REST API integration required.",
         "Swift, iOS, REST API"),
    ]
    print(f"{'Title':<35} {'Extracted skills'}")
    print("-" * 80)
    for title, desc, _ in tests:
        skills = extract_skills_from_text(f"{title} {desc}")
        print(f"{title:<35} {skills}")