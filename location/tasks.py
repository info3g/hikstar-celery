from celery.utils.log import get_task_logger

from hikster.celery import app
from hikster.helpers.functions import send_email

logger = get_task_logger(__name__)


@app.task(name='send_deletion_email_task')
def send_deletion_email_task(subject=None, message=None, from_email=None, recipient_list=None):
    logger.info("Email sent!")

    send_email(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list)
