from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, Protocol, Type, TypeGuard, TypeVar

from .models import Event


T = TypeVar("T", bound=Event)
U = TypeVar("U", bound=Event)


@dataclass
class Context(Generic[T]):
    """A context for an event."""

    event: T
    unsubscribe: Callable[[], None]


class ContextTypeChecker(Generic[U, T]):
    """A protocol for checking the type of a context."""

    def __init__(self, type_: Type[T]) -> None:
        self.type_ = type_

    def check(self, context: Context[U]) -> TypeGuard[Context[T]]:
        """Check the type of a context."""
        return isinstance(context.event, self.type_)


class Filter(Protocol[T]):
    """A filter for an event."""

    async def __call__(self, context: Context[T]) -> None:
        """Handle an event if it passes the filter."""


class RoomFilter(Filter[T]):
    """A room event filter."""

    def __init__(
        self, room_id: str, callback: Callable[[Context[T]], Awaitable[None]]
    ) -> None:
        self.room_id = room_id
        self.callback = callback

    async def __call__(self, context: Context[T]) -> None:
        """Handle an event if it is in the room."""
        if context.event._room == self.room_id:
            await self.callback(context)


class OneTimeFilter(Filter[T]):
    """A one-time event filter."""

    def __init__(self, callback: Callable[[Context[T]], Awaitable[None]]) -> None:
        self.callback = callback

    async def __call__(self, context: Context[T]) -> None:
        """Handle an event if it has not been called before."""
        await self.callback(context)
        context.unsubscribe()


class EventTypeFilter(Filter[T], Generic[T, U]):
    """A filter that filters by event type."""

    def __init__(
        self, type_: Type[U], callback: Callable[[Context[U]], Awaitable[None]]
    ) -> None:
        self.type_ = type_
        self.callback = callback

    async def __call__(self, context: Context[T]) -> None:
        """Handle an event if it is of the correct type."""
        if ContextTypeChecker[T, U](self.type_).check(context):
            await self.callback(context)


class EventDispatcher:
    """EventDispatcher class - implements a simple observer pattern
    for Matrix events."""

    def __init__(self) -> None:
        self._observers: list[Callable[[Context[Event]], Awaitable[None]]] = []

    def register(self, observer: Callable[[Context[Event]], Awaitable[None]]) -> None:
        """Register an observer."""
        self._observers.append(observer)

    def unregister(self, observer: Callable[[Context[Event]], Awaitable[None]]) -> None:
        """Unregister an observer."""
        self._observers.remove(observer)

    async def dispatch(self, event: Event) -> None:
        await asyncio.gather(
            *(
                observer(
                    Context(event=event, unsubscribe=lambda: self.unregister(observer))
                )
                for observer in self._observers
            )
        )
