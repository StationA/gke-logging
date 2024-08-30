import typing

from datetime import datetime
from enum import Enum
from pydantic import AfterValidator, AnyHttpUrl, BaseModel, Field


class LogLevel(str, Enum):
    """
    Typed str/Enum to match Google Cloud Logging's LogSeverity

    See https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity
    """

    DEFAULT = "DEFAULT"
    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"
    EMERGENCY = "EMERGENCY"


def _check_method(method: str):
    if method.lower() not in (
        "get",
        "post",
        "patch",
        "put",
        "delete",
        "options",
        "head",
        "connect",
    ):
        raise ValueError(f"Invalid HTTP method: {method}")
    return method


HttpMethod = typing.Annotated[str, AfterValidator(_check_method)]


class HttpRequest(BaseModel):
    """
    Typed model to match Google Cloud Logging's HttpRequest

    See https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#httprequest
    """

    protocol: str
    method: HttpMethod = Field(serialization_alias="requestMethod")
    url: AnyHttpUrl = Field(serialization_alias="requestUrl")
    request_size: typing.Optional[str] = Field(
        default=None, serialization_alias="requestSize"
    )
    user_agent: typing.Optional[str] = Field(
        default=None, serialization_alias="userAgent"
    )
    remote_ip: typing.Optional[str] = Field(
        default=None, serialization_alias="remoteIp"
    )
    server_ip: str = Field(serialization_alias="serverIp")
    referer: typing.Optional[str] = None
    status: typing.Optional[int] = None
    response_size: typing.Optional[str] = Field(
        default=None, serialization_alias="responseSize"
    )
    latency: typing.Optional[str] = None


class SourceLocation(BaseModel):
    """
    Typed model to match Google Cloud Logging's LogEntrySourceLocation

    See https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogEntrySourceLocation
    """

    file: str
    line: str
    function: str


class LogEntry(BaseModel):
    """
    Typed model to match Google Cloud Logging's LogEntry via "special payload fields"

    See https://cloud.google.com/logging/docs/structured-logging#special-payload-fields
    See https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry
    """

    time: datetime
    severity: LogLevel
    message: str
    http_request: typing.Optional[HttpRequest] = Field(
        default=None, serialization_alias="httpRequest"
    )
    span_id: typing.Optional[str] = Field(
        default=None, serialization_alias="logging.googleapis.com/spanId"
    )
    source_location: typing.Optional[SourceLocation] = Field(
        default=None, serialization_alias="logging.googleapis.com/sourceLocation"
    )
    labels: typing.Mapping[str, str] = Field(
        default_factory=dict, serialization_alias="logging.googleapis.com/labels"
    )
