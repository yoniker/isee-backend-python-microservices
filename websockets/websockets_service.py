from sanic import Sanic
from sanic.response import json as json_response
import json

app = Sanic("SanicChatApp")
app.config.WEBSOCKET_PING_INTERVAL = 300
app.config.WEBSOCKET_PING_TIMEOUT = 600

connected_websockets = {}

@app.route('/websockets/message_user/<user_id:str>', methods=["POST"])
async def send_user_message_by_url(request, user_id: str):
    data = request.json
    sent = await send_websocket_message(user_id=user_id, message=data)
    if sent:
        return json_response({'result': 'message_sent'})
    return json_response({'result': 'message_not_sent'})

@app.route('/websockets/healthcheck', methods=["GET"])
async def say_healthy(request):
    return json_response({'status': 'websockets service is healthy!'})


@app.websocket("/websockets/register")
async def register(request, websocket):
    user_id = request.headers.get('user_id')
    if user_id is None:
        print('no user id header was sent')
        return
    
    print(f'connected with user {user_id}')
    
    connected_websockets[user_id] = websocket
    print(f'Registered user {user_id}')
    try:
        print(f'websocket ping interval is {websocket.ping_interval}')
        await websocket.keepalive_ping()
        print(f'connection with user {user_id} was closed')
        
        if user_id in connected_websockets and connected_websockets[user_id] == websocket:
            del connected_websockets[user_id]
        await websocket.close()
    finally:
        pass


async def send_websocket_message(user_id, message):
    if user_id not in connected_websockets:
        print(f'user {user_id} not found in connected_websockets!')
        print(f'current users are {connected_websockets.keys()}')
        return False
    try:
        websocket = connected_websockets[user_id]
        await websocket.send(json.dumps(message))
        print(f'sent {message} successfully!')
        return True
    except Exception as e:
        print(f'failing ws because of exception {e}')
        return False

#ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#ssl_context.load_cert_chain(certfile='keys/dordating.crt', keyfile='keys/dordating.key')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,) #ssl=ssl_context)


'''

docker build . -t websockets:1

docker run -d --rm -p5000:5000/tcp websockets:1

'''