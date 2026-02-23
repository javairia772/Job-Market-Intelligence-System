def filter_jobs(job_list, role=None, location=None, min_salary=None, max_salary=None, experience=None):
    """
    Filters jobs based on multiple criteria.
    job_list: list of jobs (assume columns: 1-role, 2-location, 4-salary, 5-experience)
    """
    filtered = []
    for job in job_list:
        r, loc, sal, exp = job[1], job[3], job[4], job[5]  # title, location, salary, experience
        
        if role and role.lower() not in r.lower():
            continue
        if location and location.lower() not in loc.lower():
            continue
        if min_salary:
            try: 
                if float(sal) < float(min_salary):
                    continue
            except:
                continue
        if max_salary:
            try:
                if float(sal) > float(max_salary):
                    continue
            except:
                continue
        if experience and experience != exp:
            continue
        filtered.append(job)
    return filtered