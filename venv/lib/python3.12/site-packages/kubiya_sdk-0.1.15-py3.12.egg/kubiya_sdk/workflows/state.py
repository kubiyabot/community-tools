from typing import Any, Dict, Union


class WorkflowState:
    def __init__(self, initial_state: Dict[str, Any] = None):
        self._state = initial_state or {}

    def get(self, key: str, default: Any = None):
        return self._state.get(key, default)

    def set(self, key: str, value: Any):
        self._state[key] = value

    def update(self, new_state: Union[Dict[str, Any], "WorkflowState"]):
        if isinstance(new_state, dict):
            self._state.update(new_state)
        elif isinstance(new_state, WorkflowState):
            self._state.update(new_state.to_dict())
        else:
            raise TypeError(f"Unsupported state type: {type(new_state)}")

    def to_dict(self):
        return self._state.copy()

    def __getitem__(self, key: str):
        return self._state[key]

    def __setitem__(self, key: str, value: Any):
        self._state[key] = value

    def __contains__(self, key: str):
        return key in self._state

    def __str__(self):
        return str(self._state)

    def __repr__(self):
        return f"WorkflowState({self._state})"
