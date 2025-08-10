import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 检查用户是否已认证
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return
        
        self.user = self.scope["user"]
        self.room_name = f"notifications_{self.user.id}"
        self.room_group_name = f"notifications_{self.user.id}"

        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 离开房间组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'message')

        if message_type == 'mark_read':
            notification_id = text_data_json.get('notification_id')
            await self.mark_notification_read(notification_id)

    async def notification_message(self, event):
        # 发送通知消息到WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'notification_id': event.get('notification_id'),
            'notification_type': event.get('notification_type'),
        }))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 检查用户是否已认证
        if self.scope["user"] == AnonymousUser():
            await self.close()
            return
        
        self.user = self.scope["user"]
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 离开房间组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # 发送消息到房间组
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.user.username,
            }
        )

    async def chat_message(self, event):
        # 发送消息到WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
        }))
