import os
import json

try:
    from nats.aio.client import Client as NATS
    from nats.aio.errors import ErrNoServers, ErrConnectionClosed

    IS_NATS_AVAILABLE = True
except ImportError:
    IS_NATS_AVAILABLE = False


from typing import Any, Dict


class NATSManager:
    def __init__(self):
        self.nc: NATS = NATS()
        self.is_connected = False

    async def connect(self):
        if self.is_connected:
            return

        creds_file = os.getenv("NATS_CREDS")
        if not creds_file:
            print("NATS_CREDS environment variable not set")
            return

        try:
            await self.nc.connect(
                servers=["tls://connect.ngs.global:4222"],
                user_credentials=creds_file,
                connect_timeout=30,
                max_reconnect_attempts=-1,
                reconnect_time_wait=2,
            )
            print("Connected to NATS servers.")
            self.is_connected = True
        except ErrNoServers as e:
            print(f"Could not connect to any NATS server: {e}")
        except Exception as e:
            print(f"Error connecting to NATS: {e}")

    async def publish(self, subject: str, message: Dict[str, Any]):
        if not self.is_connected:
            await self.connect()

        try:
            await self.nc.publish(subject, json.dumps(message).encode())
            print(f"Published message to `{subject}`: {message}")
        except ErrConnectionClosed:
            print("Connection closed. Attempting to reconnect...")
            await self.connect()
            await self.nc.publish(subject, json.dumps(message).encode())
        except Exception as e:
            print(f"Error publishing message: {e}")

    async def publish_request(self, subject: str, message: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        if not self.is_connected:
            await self.connect()

        try:
            response = await self.nc.request(subject, json.dumps(message).encode(), timeout=timeout)
            return json.loads(response.data.decode())
        except ErrConnectionClosed:
            print("Connection closed. Attempting to reconnect...")
            await self.connect()
            response = await self.nc.request(subject, json.dumps(message).encode(), timeout=timeout)
            return json.loads(response.data.decode())
        except Exception as e:
            print(f"Error publishing request: {e}")
            raise

    async def subscribe(self, subject: str, callback):
        if not self.is_connected:
            await self.connect()

        await self.nc.subscribe(subject, cb=callback)
        print(f"Subscribed to `{subject}`.")

    async def close(self):
        if self.is_connected:
            await self.nc.close()
            self.is_connected = False
            print("Closed connection to NATS servers.")


nats_manager = NATSManager() if IS_NATS_AVAILABLE else None
