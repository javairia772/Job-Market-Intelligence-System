"""
Application constants and column indices for job tuples.
DB row order: id, title, company, location, salary, experience, skills, job_type, posted_date
"""
import os

# Column indices for job tuples (from SELECT * FROM jobs)
JOB_ID, JOB_TITLE, JOB_COMPANY, JOB_LOCATION = 0, 1, 2, 3
DEFAULT_REMOTIVE_LIMIT = 50
JOB_SALARY, JOB_EXPERIENCE, JOB_SKILLS, JOB_TYPE, JOB_POSTED_DATE = 4, 5, 6, 7, 8

APP_NAME = "Job Market Intelligence System"

# Display
SALARY_CURRENCY = "USD"
NOT_SPECIFIED = "Not specified"

def get_project_root():
    """Return project root (parent of config/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
