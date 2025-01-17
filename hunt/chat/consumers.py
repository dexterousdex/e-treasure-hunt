import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User

from hunt.models import ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):  # type: ignore[misc]
    async def connect(self) -> None:
        room_name: str = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_name = room_name
        self.room_group_name = f"chat_{room_name}"

        # Verify that the user is authenticated and is allowed into this room.
        user: User = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        username = user.get_username()
        if not room_name.startswith(f"{username}_"):
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(
        self,
        code: int,  # noqa: ARG002
    ) -> None:
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data: str) -> None:
        data = json.loads(text_data)
        message = data["message"]
        username = data["username"]
        room = data["room"]
        team = data["team"]

        await self.save_message(username, team, room, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": message, "username": username},
        )

    # Receive message from room group
    async def chat_message(self, event: dict[str, str]) -> None:
        message = event["message"]
        username = event["username"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({"message": message, "username": username})
        )

    @sync_to_async
    def save_message(
        self, username: str, team: str, room_name: str, message: str
    ) -> None:
        try:
            team_user = User.objects.get(username=team)
            ChatMessage.objects.create(
                name=username,
                team=team_user,
                room=room_name,
                content=message,
            )
        except User.DoesNotExist:
            # We don't know which team made this message, so don't save it
            pass
