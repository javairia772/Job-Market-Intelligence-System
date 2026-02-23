import csv

def export_to_csv(job_list, filename="jobs_report.csv"):
    headers = ["ID", "Role", "Location", "Company", "Salary (USD)", "Experience"]
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(job_list)
    return filename