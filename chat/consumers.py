from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import  sync_to_async
from channels.db import database_sync_to_async
from django.utils import timezone
from authentication.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        logged_user = self.scope['user']
        other_user = self.scope['url_route']['kwargs']['username']
        other_user_obj = await sync_to_async(User.objects.filter)(username=username)
        self.thread_obj = await sync_to_async(Thread.objects.get_or_create_personal_thread)(logged_user, other_user_obj)
        self.room_name = f"personal_thread_{self.thread_obj.id}" 

        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

        await self.accept()

        msg = json.dumps({
            "status": "online",
            "user" : str(logged_user.id) 
        })
        await self.channel_layer.group_send(self.room_name, {
            'type': 'chat_message',,
            "text": msg
        })
        await self.update_user_status(logged_user, 'online')

    async def disconnect(self, close_code):
        # Leave room group
        print("disconnected from room")
        await self.update_user_status(logged_user, 'offline')
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
    
    async def recieve(self, event):
