import asyncio


class StateManager:
    def __init__(self):
        self.state = {}

    def set_initial_state(self, initial_state):
        self.state.update(initial_state)

    def get_state(self):
        return self.state

    async def stream_state(self):
        # Mocking a stream; replace with actual async updates
        while True:
            yield self.get_state()
            await asyncio.sleep(1)

    def update_state(self, key, value):
        self.state[key] = value
