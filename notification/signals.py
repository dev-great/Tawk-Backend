from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
from notification.models import NotificationPost


def send_fcm_notification(fcm_token, title, body):

    fcm_server_key = "AAAA8OdunNw:APA91bEPYQKJTrbqQShAvloClb8Pwg9Mzk8SjoIgxlKF3e2yvqyuw2T4R6AHrXX_x2To7raeK8r96he3RheaHxl_OAlVPJ7Q9xRHaFis-IiKVe9Z4IS82NUDdXa7BUYsTrBWk4DSlOOT"
    fcm_url = "https://fcm.googleapis.com/fcm/send"

    # Define the message payload
    message = {
        "to": fcm_token,
        "notification": {
            "title": title,
            "body": body,
        }
    }

    # Define headers (including authorization)
    headers = {
        "Authorization": f"key={fcm_server_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(fcm_url, json=message, headers=headers)
    if response.status_code == 200:
        print("FCM notification sent successfully")
    else:
        print("Failed to send FCM notification")


@receiver(post_save, sender=NotificationPost)
def send_notification(sender, instance, **kwargs):
    # Check if the instance has a target and a non-empty FCM token
    if instance.target and instance.target.fcm_token:
        send_fcm_notification(instance.target.fcm_token,
                              instance.title, instance.body)
