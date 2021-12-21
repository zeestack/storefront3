from time import sleep

from celery import shared_task


@shared_task
def notify_customers(message):
    print("Sending 10k emails to customers.")
    print(message)
    sleep(10)
    print("10k emails were successfully sent to customers.")
