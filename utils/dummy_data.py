import random
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta

titles = ["Data Scientist", "Backend Developer", "AI Engineer", "ML Engineer", "Software Engineer"]
companies = ["TechVision", "DataSoft", "InnoTech", "Alpha Systems", "NextGen AI"]
locations = ["Lahore", "Karachi", "Islamabad"]
skills_list = ["Python", "SQL", "Machine Learning", "Django", "TensorFlow", "Pandas", "Docker"]

def generate_dummy_jobs(n=200):
    db = DatabaseManager()
    db.clear_jobs()

    for _ in range(n):
        title = random.choice(titles)
        company = random.choice(companies)
        location = random.choice(locations)
        salary = random.randint(80000, 300000)
        experience = f"{random.randint(1,5)} Years"
        skills = ", ".join(random.sample(skills_list, 3))
        job_type = random.choice(["Remote", "Onsite"])
        posted_date = (datetime.now() - timedelta(days=random.randint(0,30))).strftime("%Y-%m-%d")

        db.insert_job((title, company, location, salary, experience, skills, job_type, posted_date))

    print(f"{n} dummy jobs inserted.")