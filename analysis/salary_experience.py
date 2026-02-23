"""Analysis: salary/experience stats and chart figures (skills, salary, experience)."""
from collections import defaultdict
import re
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure

def average_salary_by_role(job_list):
    """
    Returns a dict {role: average_salary}
    Assumes salary is numeric in column index 4
    """
    salary_data = defaultdict(list)
    for job in job_list:
        role = job[1]  # Job title
        salary = job[4]  # Salary column
        try:
            salary = float(salary)
            salary_data[role].append(salary)
        except:
            continue
    avg_salary = {role: sum(salaries)/len(salaries) for role, salaries in salary_data.items() if salaries}
    return dict(sorted(avg_salary.items(), key=lambda x: x[1], reverse=True))

def experience_distribution(job_list):
    """
    from collections import defaultdict
    import re

    Returns a dict {experience: count}
    Assumes experience in years is in column index 5
    """
    exp_data = defaultdict(int)
    for job in job_list:
        exp = job[5]
        if exp:
            exp_data[exp] += 1

    # Sort by numeric value
    def extract_number(exp_str):
        match = re.search(r'\d+', exp_str)  # extract digits
        return int(match.group()) if match else 0

    return dict(sorted(exp_data.items(), key=lambda x: extract_number(x[0])))

def get_figure_salary_distribution(avg_salary_dict, top_n=10, figsize=(6, 4)):
    """Return a Figure for embedding (no show)."""
    if not avg_salary_dict:
        return None
    roles = list(avg_salary_dict.keys())[:top_n]
    salaries = [avg_salary_dict[r] for r in roles]
    fig = Figure(figsize=figsize)
    ax = fig.add_subplot(111)
    ax.barh(roles[::-1], salaries[::-1], color="#f59e0b")
    ax.set_xlabel("Average Salary")
    ax.set_title("Top Roles by Average Salary")
    fig.tight_layout()
    return fig

def get_figure_experience_distribution(job_list, figsize=(6, 4)):
    """Return a Figure for embedding (no show)."""
    exp_dist = experience_distribution(job_list)
    if not exp_dist:

    # Sort items by numeric experience
        return None
    def extract_number(exp_str):
        match = re.search(r'\d+', str(exp_str))

    # Sort items by numeric experience
        return int(match.group()) if match else 0
    sorted_items = sorted(exp_dist.items(), key=lambda x: extract_number(x[0]))
    labels, counts = zip(*sorted_items)
    fig = Figure(figsize=figsize)
    ax = fig.add_subplot(111)
    ax.bar(labels, counts, color="#f59e0b")
    ax.set_xlabel("Experience (Years)")
    ax.set_ylabel("Number of Jobs")
    ax.set_title("Job Distribution by Experience")
    for lbl in ax.get_xticklabels():
        lbl.set_rotation(45)
        lbl.set_ha("right")
    fig.tight_layout()
    return fig

def get_figure_top_skills(skill_counts, figsize=(6, 4)):
    """Return a Figure for embedding (no show). skill_counts: list of (skill, count) tuples."""
    if not skill_counts:
        return None
    skills, counts = zip(*skill_counts)
    fig = Figure(figsize=figsize)
    ax = fig.add_subplot(111)
    ax.barh(skills[::-1], counts[::-1], color="#38bdf8")
    ax.set_xlabel("Number of Job Listings")
    ax.set_title("Top In-Demand Skills")
    fig.tight_layout()
    return fig