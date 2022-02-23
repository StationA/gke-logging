import logging
import sys
import time
import typing

from datetime import datetime
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Send, Scope
from starlette.requests import Request

from .context import get_user_id, set_http_request, utcnow
from .pylogging import GKELoggingFormatter
from .types import HttpRequest


def build_http_request_from_scope(scope: Scope) -> HttpRequest:
    """
    Converts an ASGI scope into a partially-complete HttpRequest object suitable for GKE structured
    JSON logging
    """

    req = Request(scope)
    server_ip, _ = req.scope["server"]
    protocol = f"HTTP/{req.scope['http_version']}"
    return HttpRequest(
        protocol=protocol,
        method=req.method,
        url=str(req.url),
        # TODO: Confirm if this is accurate even for body-less requests
        request_size=req.headers.get("Content-Length"),
        user_agent=req.headers.get("User-Agent"),
        remote_ip=req.client.host,
        server_ip=server_ip,
        referer=req.headers.get("Referer"),
    )


class GKELoggingMiddleware:
    """
    ASGI middleware for logging access logs via Google Cloud's "structured logging" in GKE
    containers.

    Under the hood, this works by leveraging the GKELoggingFormatter and setting the httpRequest via
    contextvar scoped to each incoming request.
    """

    """
    This should reflect the "combined" common log format, commonly found in major web servers like
    Apache httpd and NGINX (https://httpd.apache.org/docs/trunk/logs.html#combined).

    The format generally contains these atoms:
        - Remote address (client IP)
        - RFC-1413 identity
        - User ID
        - Request timestamp
        - HTTP request line (i.e. "<METHOD> <REQUEST_URL> <PROTOCOL>")
        - HTTP response status code
        - HTTP response length in bytes
        - HTTP referer ("combined")
        - User agent ("combined")

    Note that a dash is used to indicate any missing data
    """
    common_log_format = " ".join(
        (
            "{remote_addr}",
            "{ident}",
            "{user_id}",
            "[{timestamp}]",
            "{request_line}",
            "{status_code}",
            "{response_length}",
            '"{referer}"',
            '"{user_agent}"',
        )
    )

    def __init__(
        self,
        app: ASGIApp,
        access_log: typing.Union[logging.Logger, str] = "asgi.access",
        access_log_message_format: str = common_log_format,
        **formatter_args,
    ):
        self._app = app
        if isinstance(access_log, str):
            self._logger = logging.Logger(access_log, level=logging.INFO)
        else:
            self._logger = access_log
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(GKELoggingFormatter(**formatter_args))
        self._logger.addHandler(h)
        self._access_log_message_format = access_log_message_format

    def log_request(self, request_time: datetime, http_request: HttpRequest):
        """
        Logs out the current request using the configured access_log_message_format
        """

        timestamp = request_time.strftime("%d/%b/%Y:%H:%M:%S %z")
        url_with_query: str = http_request.url.path or "/"
        if http_request.url.query:
            url_with_query += f"?{http_request.url.query}"
        data = dict(
            remote_addr=http_request.remote_ip,
            ident=None,
            user_id=get_user_id(),
            timestamp=timestamp,
            request_line=f"{http_request.method} {url_with_query} {http_request.protocol}",
            status_code=http_request.status,
            response_length=http_request.response_size,
            referer=http_request.referer,
            user_agent=http_request.user_agent,
        )
        data = {k: v if v is not None else "-" for k, v in data.items()}
        log_line = self._access_log_message_format.format(**data)

        # Log levels should reflect status code
        if http_request.status is None or http_request.status < 400:
            self._logger.info(log_line, extra=dict(timestamp=request_time))
        elif http_request.status < 500:
            self._logger.warning(log_line, extra=dict(timestamp=request_time))
        else:
            self._logger.error(log_line, extra=dict(timestamp=request_time))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self._app(scope, receive, send)  # pragma: no cover

        request_time = utcnow()
        http_request = build_http_request_from_scope(scope)
        set_http_request(http_request)

        async def send_wrapper(message: Message) -> None:
            """
            Wraps outgoing response stream messages in order to capture response line and header
            data that is important for logging in the httpRequest structured field
            """
            if message["type"] == "http.response.start":  # Capture response data
                http_request.status = message["status"]
                response_headers = Headers(raw=message.get("headers", {}))
                # TODO: Confirm this behavior for streaming responses
                http_request.response_size = response_headers.get("content-length")
            await send(message)

        start_time = time.time()
        try:
            # Continue along to the next set of middleware or endpoint, but with the send_wrapper
            # instead
            await self._app(scope, receive, send_wrapper)
        except Exception:
            # Set response status explicitly in the case of an uncaught exception
            # TODO: Confirm this is sane default behavior
            http_request.status = 500
            raise
        finally:
            # Finally record the total response latency and log the request to the access log
            end_time = time.time()
            http_request.latency = f"{end_time - start_time:.5f}s"
            self.log_request(request_time, http_request)
