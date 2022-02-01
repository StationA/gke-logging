import typing

from contextvars import ContextVar
from datetime import datetime, timezone

from .types import HttpRequest


LABELS: ContextVar[typing.Dict[str, str]] = ContextVar("labels")
USER_ID: ContextVar[str] = ContextVar("user_id")
SPAN_ID: ContextVar[str] = ContextVar("span_id")
REQUEST: ContextVar["HttpRequest"] = ContextVar("request")


def utcnow() -> datetime:
    """
    Helper for getting the current time in UTC
    """
    return datetime.now(tz=timezone.utc)


def set_user_id(user_id: str) -> None:
    """
    Sets the user ID for the current logging context
    """
    USER_ID.set(user_id)


def get_user_id() -> typing.Optional[str]:
    """
    Retrieves the current user ID, if it exists
    """
    return USER_ID.get(None)


def add_label(label: str, value: str) -> None:
    """
    Adds an arbitrary label to the current logging context
    """
    labels = LABELS.get({})
    labels[label] = value
    LABELS.set(labels)


def set_labels(**labels) -> None:
    """
    Sets multiple labels for the current logging context
    """
    LABELS.set(labels)


def get_labels() -> typing.Mapping[str, str]:
    """
    Retrieves the current labels, or an empty dict if none have been set
    """
    return LABELS.get({})


def set_span_id(span_id: str) -> None:
    """
    Sets the span ID for the current logging context
    """
    SPAN_ID.set(span_id)


def get_span_id() -> typing.Optional[str]:
    """
    Retrieves the current span ID, if it exists
    """
    return SPAN_ID.get(None)


def set_http_request(http_request: HttpRequest) -> None:
    """
    Sets the HttpRequest for the current logging context
    """
    REQUEST.set(http_request)


def get_http_request() -> typing.Optional[HttpRequest]:
    """
    Retrieves the current HttpRequest, if it exists
    """
    return REQUEST.get(None)
