import uvicorn
uvicorn.run('app:app',host='0.0.0.0', port=5000,ws_ping_interval=300, ws_ping_timeout=300)