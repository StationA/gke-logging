import logging
import typing

from datetime import datetime

from .context import get_http_request, get_labels, get_span_id, utcnow
from .types import LogEntry, LogLevel, SourceLocation


LabelOrGetter = typing.Union[str, typing.Callable[[logging.LogRecord], str]]


class GKELoggingFormatter(logging.Formatter):
    """
    Standard Python logging.Formatter for implementing Google Cloud's "structured logging" in GKE
    containers.

    This implementation uses optional contextvars to set some additional fields to further color
    each log entry's context:

        - spanId via set_span_id() and get_span_id()
        - httpRequest via set_http_request() and get_http_request()

    This implementation also provides for a set of default metadata labels to be defined for
    app-wide log annotations, which should be used for labeling log messages with information such
    as application identifiers, version numbers, environments, etc. These default labels can be
    expressed either as static strings, or functions that can compute a value given a LogRecord

    See https://cloud.google.com/logging/docs/structured-logging
    """

    def __init__(self, default_labels: typing.Mapping[str, LabelOrGetter] = {}):
        super().__init__()
        self._default_labels = default_labels

    def _get_labels(self, record: logging.LogRecord) -> typing.Mapping[str, str]:
        """
        Computes the labels for this log entry by merging labels in the below order:

          - "Default labels" configured on the formatter instance
          - "Contextual labels" configured in the current task context
          - LogRecord "extras" set at point of the logger use
        """
        default_labels = {
            k: v(record) if callable(v) else v for k, v in self._default_labels.items()
        }
        return {
            **default_labels,
            **get_labels(),
            **record.__dict__.get("labels", {}),
        }

    def format(self, record: logging.LogRecord) -> str:
        timestamp: datetime = record.__dict__.get("timestamp", utcnow())
        log_entry = LogEntry(
            time=timestamp.isoformat(),
            severity=LogLevel[record.levelname],
            message=super().format(record),
            http_request=get_http_request(),
            source_location=SourceLocation(
                file=record.pathname,
                line=record.lineno,
                function=record.funcName,
            ),
            span_id=get_span_id(),
            labels=self._get_labels(record),
        )
        # Output the JSON by pydantic field "alias" so that we can use non-field-friendly output
        # keys
        return log_entry.json(by_alias=True, exclude_none=True)
