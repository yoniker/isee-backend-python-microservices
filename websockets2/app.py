from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.endpoints import HTTPEndpoint
from starlette.routing import Route
from starlette.endpoints import WebSocketEndpoint
from starlette.routing import Route, WebSocketRoute
import json


websockets = dict()


class SayHealthy(HTTPEndpoint):
    async def get(self, request):
        return JSONResponse({'status': 'websockets service is healthy!'})


class RelayMessageToWebsocket(HTTPEndpoint):
    async def post(self,request):
        try:
            receiver_id = request.path_params['user_id']
            data = await request.json()
            if receiver_id not in websockets:
                JSONResponse({'result': 'message_not_sent','details':'User not found in active websockets'})
            websocket = websockets[receiver_id]
            try:
                await websocket.send(json.dumps(data))
            except Exception as e:
                if receiver_id in websockets: del websockets[receiver_id]
                raise e
            print('Success: message was sent!')
            return JSONResponse({'result': 'message_sent'})
        except:
            print('Error: message was not sent')
            return JSONResponse({'result': 'message_not_sent'})


class WebsocketBehavior(WebSocketEndpoint):
    encoding = 'json'

    async def on_connect(self, websocket):
        user_id = websocket.headers.get('user_id')
        print(f'on connect called with user_id={user_id}')
        websockets[user_id] = websocket
        await websocket.accept()

    async def on_receive(self, websocket, data):
        print('on recieve called')
        #await websocket.send_json(data={'Got this':data})
        print(f'Got this from websocket:{data}')

    async def on_disconnect(self, websocket, close_code):
        print('on disconnect called')
        try:
            user_id = websocket.headers.get('user_id')
            del websockets[user_id]
            print(f'deleted {user_id} from websockets dict')
        except:
            pass


routes = [
    Route("/websockets/healthcheck", SayHealthy),
    Route('/websockets/message_user/{user_id}',RelayMessageToWebsocket),
WebSocketRoute("/websockets/register", WebsocketBehavior)
]




app = Starlette(routes=routes)



