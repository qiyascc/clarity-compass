from clarity_api.app import create_app
from clarity_api.queue import JobQueue
from clarity_api.settings import get_settings
from clarity_persistence.jobs import create_job_app

settings = get_settings()
app = create_app(settings, JobQueue(create_job_app(settings.database_url)))
