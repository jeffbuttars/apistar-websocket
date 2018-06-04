import logging
import typing
from enum import Enum

import websockets
from apistar import App
from apistar.exceptions import HTTPException
from apistar.http import Response
from apistar.server.asgi import ASGIReceive, ASGIScope, ASGISend
from apistar.server.components import Component

logger = logging.getLogger(__name__)

class Status(Enum):
    # 1000 indicates a normal closure, meaning that the purpose for
    # which the connection was established has been fulfilled.
    OK = 1000

    # 1001 indicates that an endpoint is "going away", such as a server
    # going down or a browser having navigated away from a page.
    LEAVING = 1001

    # 1002 indicates that an endpoint is terminating the connection due
    # to a protocol error.
    PROT_ERROR = 1002

    # 1003 indicates that an endpoint is terminating the connection
    # because it has received a type of data it cannot accept (e.g., an
    # endpoint that understands only text data MAY send this if it
    # receives a binary message).
    UNSUPPORTED_TYPE = 1003

    # Reserved.  The specific meaning might be defined in the future.
    RESERVED_1004 = 1004

    # 1005 is a reserved value and MUST NOT be set as a status code in a
    # Close control frame by an endpoint.  It is designated for use in
    # applications expecting a status code to indicate that no status
    # code was actually present.
    NO_STATUS = 1005

    # 1006 is a reserved value and MUST NOT be set as a status code in a
    # Close control frame by an endpoint.  It is designated for use in
    # applications expecting a status code to indicate that the
    # connection was closed abnormally, e.g., without sending or
    # receiving a Close control frame.
    CLOSED_ABNORMAL = 1006

    # 1007 indicates that an endpoint is terminating the connection
    # because it has received data within a message that was not
    # consistent with the type of the message (e.g., non-UTF-8 [RFC3629]
    # data within a text message).
    INALID_DATA = 1007

    # 1008 indicates that an endpoint is terminating the connection
    # because it has received a message that violates its policy.  This
    # is a generic status code that can be returned when there is no
    # other more suitable status code (e.g., 1003 or 1009) or if there
    # is a need to hide specific details about the policy.
    POLICY_VIOLATION = 1008

    # 1009 indicates that an endpoint is terminating the connection
    # because it has received a message that is too big for it to
    # process.
    TOO_BIG = 1009

    # 1010 indicates that an endpoint (client) is terminating the
    # connection because it has expected the server to negotiate one or
    # more extension, but the server didn't return them in the response
    # message of the WebSocket handshake.  The list of extensions that
    TLS_FAIL = 1010


class WebSocketClosed(HTTPException):
    def __init__(self,
                 detail: str = 'WebSocket has closed',
                 status_code: int = Status.OK.value) -> None:
        super().__init__(detail, 200)

        #  def get_headers(self):
        #      return {
        #      }


class WebSocketProtocolError(HTTPException):
    def __init__(self,
                 detail: str = 'WebSocket protocol error',
                 status_code: int = Status.PROT_ERROR.value) -> None:
        super().__init__(detail, status_code)


class WebSocket(object):
    """
    Basic WebSocket wrapper for APIStar, though this one is specific to Uvicorn.

    This only works with ASGI and on a standalone route the manages connecting and closing
    the WebSocket. The WebSocketAutoHook can connect/close the connection before and after
    the handler but ASyncApp::asgi_finalize must be able to handle the websocket type
    correctly and not try to send an HTTP response.

    Something like this in ASyncApp::asgi_finalize can allow for cleaner WebSocket usage.

        # Process exceptions

        if scope.get('type') == 'websocket':
            return

        # Process HTTP Response
    """
    def __init__(self,
                 asgi_scope: dict,
                 asgi_send: typing.Callable,
                 asgi_receive: typing.Callable,
                 ) -> None:

        self.scope = asgi_scope
        self.asgi_send = asgi_send
        self.asgi_receive = asgi_receive

        # UVicorn specific, get the WebSocketRequest instance
        # This will blow up under the debug server, so we'll fake it, I guess?
        try:
            self._ws_request = asgi_send.__self__
        except AttributeError as e:
            logger.error("Unable to get a reference to underlying Uvicorn websocket instance")
            self._ws_request = None

    @property
    def state(self):
        if hasattr(self._ws_request, 'state'):
            return self._ws_request.state

        return self._ws_request.protocol.state

    @property
    def is_open(self):
        return self.state is websockets.protocol.State.OPEN

    async def send(self, data=None, **kwargs):
        msg = {
            'type': 'websocket.send',
        }

        msg.update(kwargs)

        if data:
            if isinstance(data, str):
                msg['text'] = data
            elif isinstance(data, bytes):
                msg['bytes'] = data

        return await self.asgi_send(msg)

    async def receive(self):
        msg = await self.asgi_receive()
        return msg.get('text', msg.get('bytes'))

    async def connect(self):
        # Try to accept and upgrade the websocket
        msg = await self.asgi_receive()

        if msg['type'] != 'websocket.connect':
            raise WebSocketProtocolError(
                'Expected websocket connection but got: %s' % msg['type'])

        await self.asgi_send({'type': 'websocket.accept'})

    async def close(self, code: int = Status.OK.value, data=None):
        message = {
            'type': 'websocket.disconnect',
            'code': code,
        }

        if data:
            if isinstance(data, str):
                message['text'] = data
            elif isinstance(data, bytes):
                message['bytes'] = data

        await self.asgi_send(message)


class WebSocketAutoHook():
    """
    Automatically connect the websocket on request.
    Automatically close the websocket after it's handled
    NOTE: This hook only works if AsyncApp::asgi_finalize supports the webhook type
    and doesn't send HTTP Response data when a WebSocket is finished.
    """
    async def on_request(self, ws: WebSocket):
        if ws.scope.get('type') == 'websocket':
            await ws.connect()

    async def on_response(self, ws: WebSocket, response: Response, scope: ASGIScope):
        if scope.get('type') == 'websocket' and ws.is_open:
            await ws.close(data=response.content if response else None)

    async def on_error(self, ws: WebSocket, response: Response, scope: ASGIScope):
        if scope.get('type') == 'websocket' and ws.is_open:
            await ws.close(data=response.content if response else None)


class WebSocketComponent(Component):
    def resolve(self,
                scope: ASGIScope,
                send: ASGISend,
                receive: ASGIReceive) -> WebSocket:

        return WebSocket(scope, send, receive)

