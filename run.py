"""
run.py — API'yi baslatir.
Kullanim: py -3.10 run.py
"""
import asyncio
import sys
import uvicorn
from uvicorn import Config, Server


async def main():
    config = Config(
        app="api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        loop="asyncio",
    )
    server = Server(config)
    await server.serve()


if __name__ == "__main__":
    # Windows'ta IocpProactor yerine Selector kullanilir (WinError 10014 fix)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
