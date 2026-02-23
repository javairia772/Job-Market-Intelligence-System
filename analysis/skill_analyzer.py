from collections import Counter

def extract_skills(job_list):
    """
    Extract all skills from job_list.
    Each job's skills are assumed to be a comma-separated string.
    """
    all_skills = []
    for job in job_list:
        skills_str = job[6]  # Skills column index
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]
        all_skills.extend(skills)
    return all_skills

def top_skills(job_list, top_n=10):
    """
    Returns a list of (skill, count) tuples for top N skills
    """
    all_skills = extract_skills(job_list)
    counter = Counter(all_skills)
    return counter.most_common(top_n)