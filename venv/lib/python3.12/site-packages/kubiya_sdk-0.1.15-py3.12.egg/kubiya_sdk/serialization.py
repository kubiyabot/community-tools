import inspect
from json import JSONEncoder

from pydantic import AnyUrl, BaseModel

from kubiya_sdk.tools.models import Tool, FileSpec
from kubiya_sdk.workflows.stateful_workflow import WorkflowStep, StatefulWorkflow


class KubiyaJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, StatefulWorkflow):
            return {
                "name": obj.name,
                "description": obj.description,
                "steps": {name: self.serialize_step(step) for name, step in obj.steps.items()},
                "entry_point": obj.entry_point,
            }
        elif isinstance(obj, WorkflowStep):
            return self.serialize_step(obj)
        elif isinstance(obj, Tool):
            return self.serialize_tool(obj)
        elif inspect.isfunction(obj) or inspect.ismethod(obj):
            return f"{obj.__module__}.{obj.__qualname__}"
        elif isinstance(obj, type):
            return f"{obj.__module__}.{obj.__name__}"
        elif isinstance(obj, BaseModel):
            return obj.dict()
        elif isinstance(obj, AnyUrl):  # Handle URL types here
            return str(obj)
        return super().default(obj)

    def serialize_step(self, step):
        return {
            "name": step.name,
            "description": step.description,
            "icon": step.icon,
            "label": step.label,
            "next_steps": step.next_steps,
            "conditions": step.conditions,
        }

    def serialize_tool(self, tool):
        serialized = {}
        for field, value in tool.__dict__.items():
            if field == "with_files":
                serialized[field] = self.serialize_files(value)
            elif isinstance(value, (str, int, float, bool, type(None))):
                serialized[field] = value
            elif isinstance(value, list):
                serialized[field] = [self.serialize_item(item) for item in value]
            elif isinstance(value, dict):
                serialized[field] = {k: self.serialize_item(v) for k, v in value.items()}
            elif isinstance(value, BaseModel):
                serialized[field] = value.dict()
            else:
                serialized[field] = str(value)
        return serialized

    def serialize_files(self, files):
        if files is None:
            return None
        return [self.serialize_file(file) for file in files]

    def serialize_file(self, file):
        if isinstance(file, FileSpec):
            return {
                "source": file.source,
                "destination": file.destination,
                "content": file.content,
            }
        elif isinstance(file, dict):
            return file
        else:
            return str(file)

    def serialize_item(self, item):
        if isinstance(item, (str, int, float, bool, type(None))):
            return item
        elif isinstance(item, list):  # Using 'list' instead of 'List'
            return [self.serialize_item(subitem) for subitem in item]
        elif isinstance(item, dict):  # Using 'dict' instead of 'Dict'
            return {k: self.serialize_item(v) for k, v in item.items()}
        elif isinstance(item, BaseModel):
            return item.dict()
        elif isinstance(item, AnyUrl):  # Handle URLs as strings
            return str(item)
        else:
            return str(item)
