
<p align='center'>
    <H1 align='center'> API Star WebSocket </H1>
</p>

<p align='center'>
    <em>A WebSocket Component for easily using WebSockets with API Star and Uvicorn</em>
</p>

<p align='center'>
    <a href="https://badge.fury.io/py/apistar-websocket">
    <img src="https://badge.fury.io/py/apistar-websocket.svg" alt="PyPI version" height="18">
    </a>
</p>


---

Easy WebSocket component for API Star and Uvicorn.

* [Features](#features)
* [Install](#install)
* [Examples](#examples)
    * [Uvicorn](#uvicorn)
* [Issues](#issues)

---

## Features

### It's Easy to use

Simply use it like any other component on a route handler that will accept WebSocket
connections

```python
# With WebSocketAutoHook in event_hooks is the easiest usage,
# but see the Issues below about using WebSocketAutoHook
async def ws_handler(ws: WebSocket):
    inbound_msg = await ws.recv()
    ...
    await ws.send(outbound_msg)

# Without the WebSocketAutoHook
async def ws_handler(ws: WebSocket):
    await ws.connect()
    inbound_msg = await ws.recv()
    ...
    await ws.send(outbound_msg)
    await ws.close()
```

### Auto connecting and closing event hook.

When used with the `WebSocketAutoHook` the WebSocket will be connected before the handler
is called. When the handler returns or is ended due to error the WebSocket will be automatically
closed. See the [Issues](#issues) below concerning `WebSocketAutoHook`.

## Install

    pip install apistar-websocket

or for [Pipenv](https://docs.pipenv.org/) users

    pipenv install apistar-websocket


## Examples

Here's a basic example of sending 100 numbers to the connected client and waiting
for a return message after each send. The WebSocket is connected and closed for us
by the `WebSocketAutoHook`.

```python
import json
from apistar import ASyncApp, Route
from websocket import WebSocket, WebSocketComponent, WebSocketAutoHook


async def welcome_ws(path: str, ws: WebSocket):
    """
    A WebSocket endpoint used to play a terrible game of data ping pong.
    """
    for i in range(100):
        await ws.send(
            json.dumps({
                "msg": f"{path} is nice",
                "count": i,
            })
        )

        # We'll pretend we're playing ping pong
        msg = await ws.receive()

routes = [
    Route('/{+path}', 'GET', handler=welcome_ws, name='welcome_ws'),
]

event_hooks = [WebSocketAutoHook]
components = [WebSocketComponent()]

app = ASyncApp(
    routes=routes,
    components=components,
    event_hooks=event_hooks,
)


if __name__ == '__main__':
    main()
```

Same example as above, but without using the `WebSocketAutoHook`. Here the handler
must manage the WebSocket connection itself and run as a standalone `Route` to prevent
API Star from sending responses to the client.
```python
import json
from apistar import ASyncApp, Route
from websocket import WebSocket, WebSocketComponent


async def welcome_ws(path: str, ws: WebSocket):
    """
    A WebSocket endpoint used to subscribe to a stream of data.
    """

    # finish the connection
    await.connect()

    for i in range(100):
        await ws.send(
            json.dumps({
                "msg": f"{path} is nice",
                "count": i,
            })
        )

        # We'll pretend we're playing ping pong
        msg = await ws.receive()

    # close the connection
    await ws.close()

# Must run the route standalone to prevent the attempt at an HTTP Response being sent
routes = [
    Route('/{+path}', 'GET', handler=welcome_ws, name='welcome_ws', standalone=True),
]

components = [WebSocketComponent()]

app = ASyncApp(
    routes=routes,
    components=components,
)


if __name__ == '__main__':
    main()
```

## Uvicorn
You have to run your API Star with Uvicorn for `apistar-websocket` to work.

To run you app with debug on and automatically reloading the app on file changes,
great for development, use:

    uvicorn --log-level DEBUG --reload app:app

For a production environment start from the command:

    uvicorn app:app

And adjust as needed, see `uvicorn --help` for more options.

## Issues

The cleanest way to use the component is without the `WebSocketAutoHook` and as a standalone
route with the handler connecting and closing the WebSocket. This is because when a handler is
_not_ used as a standalone route, the default, API Star will send an HTTP response after a handler
has finished. While this needed for regular HTTP requests, it is not for
WebSocket connections as they are already closed. You can use the `WebSocketAutoHook`
and your handlers will function as you expect.
But to prevent API Star from sending the HTTP response
`WebSocketAutoHook` will raise an exception after closing the WebSocket to prevent the HTTP
response causing an error condition in API Star.
