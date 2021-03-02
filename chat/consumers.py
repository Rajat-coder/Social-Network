from authentication.models import User
from channels.consumer import  AsyncConsumer
from asgiref.sync import  sync_to_async
from fcm_django.models import FCMDevice
from .models import Thread, Message, ConnectionHistory
import json
from channels.db import database_sync_to_async
from datetime import datetime


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        me = self.scope['user']
        other_username = self.scope['url_route']['kwargs']['username']
        other_user = await sync_to_async(User.objects.get)(username=other_username)
        self.thread_obj = await sync_to_async(Thread.objects.get_or_create_personal_thread)(me, other_user)
        self.room_name = f'personal_thread_{self.thread_obj.id}'

        await self.channel_layer.group_add(self.room_name, self.channel_name)
       
        await self.send({
            'type': 'websocket.accept',
        })
        msg = json.dumps({
            "status": "online",
            "user" : str(me) 
        })
        await self.channel_layer.group_send(self.room_name,
                                            {
                                                'type': 'websocket.message',
                                                "text": msg
                                            }
                                            )
        await self.update_user_status(me, 'online')
        print(f'[{self.channel_name}] - You are connected')
        

    async def websocket_receive(self, event):
        other_username = self.scope['url_route']['kwargs']['username']
        a = await sync_to_async (User.objects.get)(username = other_username)
        status = await sync_to_async(ConnectionHistory.objects.get)(user = a)
        # me = self.scope['user']
        # me = await sync_to_async (User.objects.get)(username = me)
        msg = json.dumps({
            'text': event.get('text'),
            'username': self.scope['user'].username
        })

        if status.status == 'offline':
            await self.store_message(event.get('text'))
            # FcmNotification = await sync_to_async(FCMDevice.objects.get)(user = a)
            # text = f"{me.first_name} {me.last_name} sent you a message"
            # await FcmNotification.send_message(text,event.get('text') )

        await self.channel_layer.group_send(self.room_name,
                                            {
                                                'type': 'websocket.message',
                                                "text": msg
                                            }
                                            )

    async def websocket_message(self, event):
        await self.send({
            'type': 'websocket.send',
            "text": event["text"],
        }
        )

    async def websocket_disconnect(self, event):
        me = self.scope['user']
        await self.update_user_status(me, 'offline')
        msg = json.dumps({
            "status": "offline",
            "user": str(me)
        })
        await self.channel_layer.group_send(self.room_name,
                                            {
                                                'type': 'websocket.message',
                                                "text": msg
                                            }
                                            )
        await self.update_user_status(me, 'offline')
        print("websocket closed", me)
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    @database_sync_to_async
    def store_message(self, text):
        Message.objects.create(
            thread=self.thread_obj,
            sender=self.scope['user'],
            text=text
        )
        # notifier = self.scope['url_route']['kwargs']['username']
        # a = User.objects.get(username = notifier)
        # FCM_Token = FCMDevice.objects.get(user = a).late
        # me = self.scope['user']
        # me = User.objects.get(username = me)
        # text = f"{me.first_name} {me.last_name} sent you a message"
        # FCM_Token.send_message("Message", text )
        


    @database_sync_to_async
    def update_user_status(self, user, status):
        cnt = ConnectionHistory.objects.filter(user=user).update(status=status, last_seen = datetime.now())
        if cnt == 0:
            ConnectionHistory.objects.create(user = user, status=status, last_seen = datetime.now())
            cnt = 1
        return cnt