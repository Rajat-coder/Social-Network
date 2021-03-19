from friends.models import FriendRequest
from fcm_django.models import FCMDevice
from shared.utils import send_fcm_notification

def req_sent_message(user_full_name):
    return f"{user_full_name} sent you friend request"

def accept_request_message(user_full_name):
    return f"{user_full_name} accepted your friend request"

def req_sent_noti(receiver_id, user_full_name):
    devices = FCMDevice.objects.filter(user_id = receiver_id, active= True)
    send_fcm_notification(
        devices,
        title = "Friend Request",
        body = req_sent_message(user_full_name),
        data = {
            "type": "Gupshup",
            "request": True,
        }
    )

def req_accpt_noti(receiver_id, user_full_name):
    devices = FCMDevice.objects.filter(user_id = receiver_id, active= True)
    send_fcm_notification(
        devices,
        title = "Friend Request",
        body = accept_request_message(user_full_name),
        data = {
            "type": "Gupshup",
            "request": True,
        }
    )

