import typing

from datetime import datetime
from enum import Enum
from pydantic import AnyHttpUrl, BaseModel, Field


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


class HttpMethod(str):
    """
    Typed str to match valid HTTP methods
    """

    ALLOWED_METHODS = (
        "get",
        "post",
        "patch",
        "put",
        "delete",
        "options",
        "head",
        "connect",
    )

    @classmethod
    def __get_validators__(clss):
        yield clss.validate

    @classmethod
    def validate(clss, v):
        if v.lower() not in HttpMethod.ALLOWED_METHODS:
            raise ValueError(f"Invalid HTTP method: {v}")
        return clss(v)


class HttpRequest(BaseModel):
    """
    Typed model to match Google Cloud Logging's HttpRequest

    See https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#httprequest
    """

    protocol: str
    method: HttpMethod = Field(alias="requestMethod")
    url: AnyHttpUrl = Field(alias="requestUrl")
    request_size: typing.Optional[str] = Field(None, alias="requestSize")
    user_agent: typing.Optional[str] = Field(None, alias="userAgent")
    remote_ip: str = Field(alias="remoteIp")
    server_ip: str = Field(alias="serverIp")
    referer: typing.Optional[str] = None
    status: typing.Optional[int] = None
    response_size: typing.Optional[str] = Field(None, alias="responseSize")
    latency: typing.Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class SourceLocation(BaseModel):
    """
    Typed model to match Google Cloud Logging's LogEntrySourceLocation

    See https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogEntrySourceLocation
    """

    file: str
    line: str
    function: str

    class Config:
        allow_population_by_field_name = True


class LogEntry(BaseModel):
    """
    Typed model to match Google Cloud Logging's LogEntry via "special payload fields"

    See https://cloud.google.com/logging/docs/structured-logging#special-payload-fields
    See https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry
    """

    time: datetime
    severity: LogLevel
    message: str
    http_request: typing.Optional[HttpRequest] = Field(alias="httpRequest")
    span_id: typing.Optional[str] = Field(None, alias="logging.googleapis.com/spanId")
    source_location: typing.Optional[SourceLocation] = Field(
        None, alias="logging.googleapis.com/sourceLocation"
    )
    labels: typing.Mapping[str, str] = Field({}, alias="logging.googleapis.com/labels")

    class Config:
        allow_population_by_field_name = True
