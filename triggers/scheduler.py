import time
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

TRIGGER_URL = "http://127.0.0.1:8001/trigger"

def job_erp():
    try: requests.post(f"{TRIGGER_URL}/erp")
    except: pass

def job_portal():
    try: requests.post(f"{TRIGGER_URL}/portal")
    except: pass

def job_email():
    try: requests.post(f"{TRIGGER_URL}/email")
    except: pass

def job_run_all():
    try: requests.post(f"{TRIGGER_URL}/run-all")
    except: pass

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(job_erp, IntervalTrigger(minutes=5, jitter=30), id='job_erp')
    scheduler.add_job(job_portal, IntervalTrigger(minutes=10, jitter=30), id='job_portal')
    scheduler.add_job(job_email, IntervalTrigger(minutes=15, jitter=30), id='job_email')
    scheduler.add_job(job_run_all, IntervalTrigger(minutes=30, jitter=30), id='job_run_all')
    
    scheduler.start()
    print("APScheduler started.")
    return scheduler

def get_schedule(scheduler):
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        })
    return jobs
