from authentication.models import User
from channels.consumer import  AsyncConsumer
from asgiref.sync import  sync_to_async
from fcm_django.models import FCMDevice
from .models import *
import json
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        me = self.scope['user']
        other_id = self.scope['url_route']['kwargs']['id']
        other_user = await sync_to_async(User.objects.get)(id=other_id)
        self.thread_obj = await sync_to_async(Thread.objects.get_or_create_personal_thread)(me, other_user)
        self.room_name = f'personal_thread_{self.thread_obj.id}'

        await self.channel_layer.group_add(self.room_name, self.channel_name)
       
        await self.send({
            'type': 'websocket.accept',
        })
        msg = json.dumps({
            "status": "online",
            "user" : str(me.id) 
        })
        await self.channel_layer.group_send(self.room_name, {
            'type': 'websocket.message',
            "text": msg
        })
        await self.update_user_status(me, 'online')

    async def websocket_receive(self, event):
        other_id = self.scope['url_route']['kwargs']['id']
        a = await sync_to_async (User.objects.get)(id = other_id)
        status = await sync_to_async(ConnectionHistory.objects.get)(user = a)
        # me = self.scope['user']
        # me = await sync_to_async (User.objects.get)(username = me)
        event_text=event.get("text")
        msg = json.dumps({
            'text': event_text,
            'user_id': self.scope['user'].id
        })
        await self.backup_message(event_text)
        if status.status == 'offline':
            await self.store_message(event_text)
            # FcmNotification = await sync_to_async(FCMDevice.objects.get)(user = a)
            # text = f"{me.first_name} {me.last_name} sent you a message"
            # await FcmNotification.send_message(text,event.get('text') )

        await self.channel_layer.group_send(self.room_name, {
            'type': 'websocket.message',
            "text": msg
        })

    async def websocket_message(self, event):
        await self.send({
            'type': 'websocket.send',
            "text": event["text"],
        })

    async def websocket_disconnect(self, event):
        me = self.scope['user']
        await self.update_user_status(me, 'offline')
        msg = json.dumps({
            "status": "offline",
            "user": str(me.id)
        })
        await self.channel_layer.group_send(self.room_name, {
            'type': 'websocket.message',
            "text": msg
        })
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    @database_sync_to_async
    def store_message(self, text):
        Message.objects.create(
            thread=self.thread_obj,
            sender=self.scope['user'],
            text=text
        )

        notifier = self.scope['url_route']['kwargs']['id']
        me = self.scope['user']
        status_check=ConnectionHistory.objects.get(user=me)
        
    
        FCM_Token = FCMDevice.objects.filter(user = notifier).latest('id')
        text = f"{me.first_name} {me.last_name} sent you a message"
        FCM_Token.send_message("Message", text , data = {"chat":True,"id":me.id,"profile":me.profile_image.url,"status":status_check.status,"username":me.username,"name": f"{me.first_name} {me.last_name}"})

    @database_sync_to_async
    def backup_message(self, text):
        BackupMessage.objects.create(
            thread=self.thread_obj,
            sender=self.scope['user'],
            text=text
        )

    @database_sync_to_async
    def update_user_status(self, user, status):
        cnt = ConnectionHistory.objects.filter(user=user).update(status=status, last_seen = timezone.now())
        if cnt == 0:
            ConnectionHistory.objects.create(user = user, status=status, last_seen = timezone.now())
            cnt = 1
        return cnt


