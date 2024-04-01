import asyncio
import uuid

import aiohttp

from matrix_client.observer_factory import ObserverFactory

from .authentication import Authentication
from .event_dispatcher import EventDispatcher
from .models import (
    Event,
    MessageEditEvent,
    MessageEvent,
    Myself,
    RedactionEvent,
    Room,
    User,
)


class Client:
    """Represents a client for the bot."""

    def __init__(self, homeserver_url: str) -> None:
        self.homeserver_url = homeserver_url
        self.authentication = Authentication(homeserver_url)

        self.next_batch = ""
        self.processed_event_ids: set[str] = set()
        self.events: list[Event] = []
        self.new_events: list[Event] = []

        self.room_evt_queues: dict[str, asyncio.Queue[Event]] = {}
        self.event_observer = EventDispatcher()

        self.room_state: dict[str, dict] = {}

    @property
    def on(self) -> ObserverFactory:
        """Return the observer factory."""
        return ObserverFactory(self.event_observer)

    def get_event(self, event_id: str) -> Event | None:
        """Get an event."""
        for event in self.events + self.new_events:
            if event.event_id == event_id:
                return event
        return None

    async def login(self, username: str, password: str) -> None:
        """Login to the homeserver."""
        await self.authentication.password_auth(username, password)

    async def get_token(self) -> str:
        """Return the token."""
        return await self.authentication.get_token()

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make a request to the homeserver."""
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f"{self.homeserver_url}/{endpoint}",
                headers=kwargs.pop("headers", {})
                | {"Authorization": f"Bearer {await self.get_token()}"},
                **kwargs,
            ) as response:
                if response.status == 429:
                    time = int(response.headers["Retry-After"])
                    await asyncio.sleep(time)
                    return await self._request(method, endpoint, **kwargs)
                return await response.json()

    async def _download_mxc(self, mxc: str) -> bytes:
        """Download an mxc."""
        server_name, media_id = mxc[6:].split("/")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.homeserver_url}/_matrix/media/v3/download/{server_name}/{media_id}",
                headers={"Authorization": f"Bearer {await self.get_token()}"},
            ) as response:
                return await response.read()

    async def _send_event(self, room_id: str, event_type: str, content: dict) -> None:
        """Send an event to a room."""
        await self._request(
            "PUT",
            f"_matrix/client/v3/rooms/{room_id}/send/{event_type}/{uuid.uuid4()}",
            json=content,
        )

    async def send_text_message(
        self, room_id: str, content: str, reply_to: str | None = None
    ) -> None:
        """Send a text message to a room."""
        await self._send_event(
            room_id,
            "m.room.message",
            {
                "msgtype": "m.text",
                "body": content,
            }
            if reply_to is None
            else {
                "msgtype": "m.text",
                "body": content,
                "m.relates_to": {"m.in_reply_to": {"event_id": reply_to}},
            },
        )

    async def send_redaction(
        self, room_id: str, event_id: str, reason: str | None = None
    ) -> None:
        """Send a redaction to a room."""
        await self._send_event(
            room_id,
            "m.room.redaction",
            {
                "redacts": event_id,
            }
            if reason is None
            else {
                "redacts": event_id,
                "reason": reason,
            },
        )

    async def whoami(self) -> Myself:
        """Get information about the authenticated user."""
        user = await self._request("GET", "_matrix/client/v3/account/whoami")
        return Myself(
            self,
            device_id=user.get("device_id"),
            user_id=user.get("user_id"),
        )

    async def get_user(self, user_id: str) -> User | None:
        """Get information about a user."""
        user = await self._request("GET", f"_matrix/client/v3/profile/{user_id}")
        if not user:
            return None
        return User(
            self,
            user_id=user_id,
            displayname=user.get("displayname"),
            avatar_url=user.get("avatar_url"),
        )

    def get_room(self, room_id: str) -> Room | None:
        """Get information about a room."""
        return Room(self, room_id, state=self.room_state.get(room_id, {}))

    async def handle_message_event(self, room_id: str, event: dict) -> None:
        """Handle a message event."""
        if (
            event.get("content", {}).get("m.relates_to", {}).get("rel_type")
            == "m.replace"
        ):
            edit = MessageEditEvent(
                self,
                event["type"],
                event,
                event["sender"],
                room_id,
                event["unsigned"]["age"],
                event["event_id"],
                None,
                event["content"],
            )
            self.new_events.append(edit)
            if edit.original:
                edit.original.edits.append(edit)
        else:
            self.new_events.append(
                MessageEvent(
                    self,
                    event["type"],
                    event,
                    event["sender"],
                    room_id,
                    event["unsigned"]["age"],
                    event["event_id"],
                    None,
                    event["content"],
                )
            )

    async def handle_redaction_event(self, room_id: str, event: dict) -> None:
        """Handle a redaction event."""
        redaction = RedactionEvent(
            self,
            event["type"],
            event,
            event["sender"],
            room_id,
            event["unsigned"]["age"],
            event["event_id"],
            None,
            event["content"],
        )
        self.new_events.append(redaction)
        if redaction.redacts:
            redaction.redacts.redacted = redaction

    async def handle_event(self, room_id: str, event: dict) -> None:
        """Handle an event."""
        if event["event_id"] in self.processed_event_ids:
            return
        self.processed_event_ids.add(event["event_id"])
        match event["type"]:
            case "m.room.message":
                await self.handle_message_event(room_id, event)
            case "m.room.redaction":
                await self.handle_redaction_event(room_id, event)
            case _:
                self.new_events.append(
                    Event(
                        self,
                        event["type"],
                        event,
                        event["sender"],
                        room_id,
                        event["unsigned"]["age"],
                        event["event_id"],
                        None,
                    )
                )

    async def sync(self) -> None:
        """Sync with the homeserver."""
        is_initial = not self.next_batch
        self.new_events.clear()
        response = await self._request(
            "GET",
            "_matrix/client/v3/sync",
            params=self.next_batch and {"since": self.next_batch},
        )
        self.next_batch = response.get("next_batch", "")
        for room_id, room in response.get("rooms", {}).get("join", {}).items():
            self.room_state[room_id] = room.get("state", {})
            for event in room.get("timeline", {}).get("events", []):
                await self.handle_event(room_id, event)
        self.events.extend(self.new_events)
        if not is_initial:
            for event in self.new_events:
                queue = self.room_evt_queues.get(event._room)
                if queue is None:
                    queue = self.room_evt_queues[event._room] = asyncio.Queue()
                    asyncio.create_task(self.run_event_observers(event._room))
                await queue.put(event)
        self.new_events = []

    async def run_event_observers(self, room_id: str) -> None:
        """Run the event observers."""
        while True:
            event = await self.room_evt_queues[room_id].get()
            await self.event_observer.dispatch(event)

    async def mainloop(self) -> None:
        """Start the client."""
        while True:
            await self.sync()

    async def run_forever(self, username: str, password: str) -> None:
        """Run the client forever."""
        await self.login(username, password)
        await self.mainloop()

    def run(self, username: str, password: str) -> None:
        """Run the client."""
        asyncio.run(self.run_forever(username, password))
