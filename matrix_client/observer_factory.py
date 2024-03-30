from __future__ import annotations
from typing import Awaitable, Callable, Type, TypeVar, overload

from .event_dispatcher import (
    Context,
    EventDispatcher,
    EventTypeFilter,
    OneTimeFilter,
    RoomFilter,
)
from .models import Event, MessageEditEvent, MessageEvent


T = TypeVar("T", bound=Event)


class ObserverFactory:
    """Represents an observer factory."""

    def __init__(self, event_dispatcher: EventDispatcher) -> None:
        self.event_dispatcher = event_dispatcher

    @overload
    def __call__(
        self,
        func: Callable[[Context[T]], Awaitable[None]],
        *,
        room: str | None,
        once: bool,
        on: Type[T],
    ) -> Callable[[Context[T]], Awaitable[None]]:
        ...

    @overload
    def __call__(
        self,
        func: Callable[[Context[Event]], Awaitable[None]],
        *,
        room: str | None,
        once: bool,
        on: None,
    ) -> Callable[[Context[Event]], Awaitable[None]]:
        ...

    @overload
    def __call__(
        self,
        func: None,
        *,
        room: str | None,
        once: bool,
        on: Type[T],
    ) -> Callable[
        [Callable[[Context[T]], Awaitable[None]]],
        Callable[[Context[T]], Awaitable[None]],
    ]:
        ...

    @overload
    def __call__(
        self,
        func: Type[T],
        *,
        room: str | None,
        once: bool,
        on: None,
    ) -> Callable[
        [Callable[[Context[T]], Awaitable[None]]],
        Callable[[Context[T]], Awaitable[None]],
    ]:
        ...

    @overload
    def __call__(
        self,
        func: None,
        *,
        room: str | None,
        once: bool,
        on: None,
    ) -> Callable[
        [Callable[[Context[Event]], Awaitable[None]]],
        Callable[[Context[Event]], Awaitable[None]],
    ]:
        ...

    def __call__(
        self,
        func: Callable[[Context[T]], Awaitable[None]] | Type[T] | None = None,
        *,
        room: str | None = None,
        once: bool = False,
        on: Type[T] | None = None,
    ) -> (
        Callable[[Context[T]], Awaitable[None]]
        | Callable[[Context[Event]], Awaitable[None]]
        | Callable[
            [Callable[[Context[T]], Awaitable[None]]],
            Callable[[Context[T]], Awaitable[None]],
        ]
        | Callable[
            [Callable[[Context[Event]], Awaitable[None]]],
            Callable[[Context[Event]], Awaitable[None]],
        ]
    ):
        """Create an observer."""
        if isinstance(func, type):

            def with_on(
                func_: Callable[[Context[T]], Awaitable[None]]
            ) -> Callable[[Context[T]], Awaitable[None]]:
                return self(func_, room=room, once=once, on=func)

            return with_on

        if func is None:

            def decorator(
                func: Callable[[Context[T]], Awaitable[None]]
            ) -> Callable[[Context[T]], Awaitable[None]]:
                # The overloads are way too complicated for mypy to handle :3
                return self(func, room=room, once=once, on=on)

            return decorator

        observer = func

        if once:
            observer = OneTimeFilter[T](observer)

        if room is not None:
            observer = RoomFilter[T](room, observer)

        # The last thing we do is erasing the type
        # Over here func is certainly a callable, therefore if "on" is None,
        # the generic type T wasn't set -> we act as if it's Event, as per the
        # overloads
        assignable: Callable[[Context[Event]], Awaitable[None]] = (
            observer if on is None else EventTypeFilter[Event, T](on, observer)
        )  # type: ignore

        self.event_dispatcher.register(assignable)

        return func

    def event(
        self,
        func: Callable[[Context[Event]], Awaitable[None]] | None = None,
        *,
        room: str | None = None,
        once: bool = False,
    ) -> (
        Callable[[Context[Event]], Awaitable[None]]
        | Callable[
            [Callable[[Context[Event]], Awaitable[None]]],
            Callable[[Context[Event]], Awaitable[None]],
        ]
    ):
        """Create an event observer."""
        return self(func, room=room, once=once, on=None)

    @overload
    def message(
        self,
        func: Callable[[Context[MessageEvent]], Awaitable[None]],
        *,
        room: str | None = None,
        once: bool = False,
    ) -> Callable[[Context[MessageEvent]], Awaitable[None]]:
        ...

    @overload
    def message(
        self,
        func: None = None,
        *,
        room: str | None = None,
        once: bool = False,
    ) -> Callable[
        [Callable[[Context[MessageEvent]], Awaitable[None]]],
        Callable[[Context[MessageEvent]], Awaitable[None]],
    ]:
        ...

    def message(
        self,
        func: Callable[[Context[MessageEvent]], Awaitable[None]] | None = None,
        *,
        room: str | None = None,
        once: bool = False,
    ) -> (
        Callable[[Context[MessageEvent]], Awaitable[None]]
        | Callable[
            [Callable[[Context[MessageEvent]], Awaitable[None]]],
            Callable[[Context[MessageEvent]], Awaitable[None]],
        ]
    ):
        """Create a message observer."""
        return self(func, room=room, once=once, on=MessageEvent)

    @overload
    def edit(
        self,
        func: Callable[[Context[MessageEditEvent]], Awaitable[None]],
        *,
        room: str | None = None,
        once: bool = False,
    ) -> Callable[[Context[MessageEditEvent]], Awaitable[None]]:
        ...

    @overload
    def edit(
        self,
        func: None = None,
        *,
        room: str | None = None,
        once: bool = False,
    ) -> Callable[
        [Callable[[Context[MessageEditEvent]], Awaitable[None]]],
        Callable[[Context[MessageEditEvent]], Awaitable[None]],
    ]:
        ...

    def edit(
        self,
        func: Callable[[Context[MessageEditEvent]], Awaitable[None]] | None = None,
        *,
        room: str | None = None,
        once: bool = False,
    ) -> (
        Callable[[Context[MessageEditEvent]], Awaitable[None]]
        | Callable[
            [Callable[[Context[MessageEditEvent]], Awaitable[None]]],
            Callable[[Context[MessageEditEvent]], Awaitable[None]],
        ]
    ):
        """Create an edit observer."""
        return self(func, room=room, once=once, on=MessageEditEvent)
