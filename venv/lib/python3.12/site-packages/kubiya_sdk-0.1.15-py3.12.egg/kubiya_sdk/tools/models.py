import os
from typing import Any, Dict, List, Union, Literal, Optional

from pydantic import Field, HttpUrl, BaseModel, constr, validator

MAX_DESCRIPTION_LENGTH = 1024


class Source(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None


class Arg(BaseModel):
    name: str
    type: Optional[Literal["str", "array", "bool", "int", "float"]] = None
    description: constr(max_length=MAX_DESCRIPTION_LENGTH)
    required: Optional[bool] = None
    default: Optional[Union[str, List[Any], bool, int, float]] = None
    options: Optional[List[str]] = None
    options_from: Optional[Dict[str, str]] = None

    @validator("type")
    def validate_type(cls, v):
        if v is not None:
            type_mapping = {
                "str": "string",
                "array": "array",
                "bool": "boolean",
                "int": "integer",
                "float": "float",
            }
            return type_mapping.get(v, v)
        return v

    @validator("default")
    def validate_default(cls, v, values):
        if v is not None and "type" in values:
            expected_type = values["type"]
            if expected_type == "str" and not isinstance(v, str):
                raise ValueError("Default value must be a string for argument of type 'str'")
            elif expected_type == "array" and not isinstance(v, list):
                raise ValueError("Default value must be a list for argument of type 'array'")
            elif expected_type == "bool" and not isinstance(v, bool):
                raise ValueError("Default value must be a boolean for argument of type 'bool'")
            elif expected_type == "int" and not isinstance(v, int):
                raise ValueError("Default value must be an integer for argument of type 'int'")
            elif expected_type == "float" and not isinstance(v, float):
                raise ValueError("Default value must be a float for argument of type 'float'")
        return v


class ToolOutput(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    output: Any


class FileSpec(BaseModel):
    source: Optional[str] = None
    destination: str
    content: Optional[str] = None

    def expand_full_name(self) -> str:
        return f"{os.path.expandvars(self.source)}:{os.path.expandvars(self.destination)}"

    def expand_source(self) -> str:
        return os.path.expandvars(self.source)

    def expand_destination(self) -> str:
        return os.path.expandvars(self.destination)

    def valid(self) -> bool:
        return self.source is not None and self.destination is not None


class Volume(BaseModel):
    path: str
    name: str

    def valid(self) -> bool:
        return len(self.path) > 0 and len(self.name) > 0

    def expand_full_name(self) -> str:
        return f"{os.path.expandvars(self.name)}:{os.path.expandvars(self.path)}"


class ServiceSpec(BaseModel):
    name: str
    image: str
    env: Optional[Dict[str, str]] = Field(default_factory=dict)
    entrypoint: Optional[List[str]] = Field(default_factory=list)
    exposed_ports: Optional[List[int]] = Field(default_factory=list)
    volumes: Optional[List[Volume]] = Field(default_factory=list)

    def endpoint(self) -> str:
        return f"{self.name}-svc:{self.exposed_ports[0]}"


class GitRepoSpec(BaseModel):
    url: str
    branch: Optional[str] = None
    dir: Optional[str] = None

    def clone_token_cmd(self, token: str) -> str:
        if token:
            return f"git clone --branch {self.branch} https://{token}@{self.url} {self.dir}"
        else:
            return f"git clone --branch {self.branch} {self.url} {self.dir}"

    def valid(self) -> bool:
        return self.url is not None and self.dir is not None


class OpenAPISpec(BaseModel):
    url: str

    def valid(self) -> bool:
        return self.url is not None


class Tool(BaseModel):
    name: str
    source: Optional[Source] = None
    alias: Optional[str] = None
    description: constr(max_length=MAX_DESCRIPTION_LENGTH)
    type: Literal["python", "golang", "docker"] = "docker"
    content: Optional[str] = None
    content_url: Optional[HttpUrl] = None
    args: List[Arg] = Field(default_factory=list)
    env: List[str] = Field(default_factory=list)
    secrets: Optional[List[str]] = Field(default_factory=list)
    dependencies: Optional[str] = None
    dependencies_url: Optional[HttpUrl] = None
    openapi: Optional[OpenAPISpec] = None
    with_files: Optional[List[FileSpec]] = Field(default_factory=list)
    with_services: Optional[List[ServiceSpec]] = Field(default_factory=list)
    with_git_repo: Optional[GitRepoSpec] = None
    with_volumes: Optional[List[Volume]] = Field(default_factory=list)
    entrypoint: Optional[List[str]] = Field(default_factory=list)
    icon_url: Optional[HttpUrl] = None
    image: Optional[str] = None
    long_running: Optional[bool] = False
    on_start: Optional[str] = None
    on_build: Optional[str] = None
    on_complete: Optional[str] = None
    mermaid: Optional[str] = None
    workflow: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        populate_by_name = True

    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        validated_inputs = {}
        for arg in self.args:
            if arg.required and arg.name not in inputs:
                raise ValueError(f"Required argument '{arg.name}' is missing")

            if arg.name in inputs:
                value = inputs[arg.name]
                if arg.type:
                    try:
                        value = self._convert_type(value, arg.type)
                    except ValueError:
                        raise ValueError(f"Invalid type for argument '{arg.name}'. Expected {arg.type}")

                if arg.options and value not in arg.options:
                    raise ValueError(
                        f"Invalid value for argument '{arg.name}'. Must be one of: {', '.join(arg.options)}"
                    )

                validated_inputs[arg.name] = value
            elif arg.default is not None:
                validated_inputs[arg.name] = arg.default

        return validated_inputs

    @staticmethod
    def _convert_type(value: Any, type_str: str) -> Any:
        if type_str == "string":
            return str(value)
        elif type_str == "integer":
            return int(value)
        elif type_str == "float":
            return float(value)
        elif type_str == "boolean":
            return bool(value)
        elif type_str == "array":
            return list(value)
        else:
            raise ValueError(f"Unsupported type: {type_str}")

    def get_image(self) -> str:
        return self.image if self.image else "alpine"

    def to_mermaid(self):
        def escape(s):
            return str(s).replace('"', '\\"').replace("\n", "<br/>")

        mermaid = [
            "graph TD",
            "    %% Styles",
            "    classDef triggerClass fill:#3498db,color:#fff,stroke:#2980b9,stroke-width:2px,font-weight:bold",
            "    classDef paramClass fill:#2ecc71,color:#fff,stroke:#27ae60,stroke-width:2px",
            "    classDef execClass fill:#e74c3c,color:#fff,stroke:#c0392b,stroke-width:2px,font-weight:bold",
            "    classDef envClass fill:#f39c12,color:#fff,stroke:#f1c40f,stroke-width:2px",
            "",
            "    %% Main Components",
            '    Trigger("Trigger"):::triggerClass',
            '    Params("Parameters"):::paramClass',
            f'    Exec("{escape(self.name)}"):::execClass',
            '    Env("Environment"):::envClass',
            "",
            "    %% Flow",
            "    Trigger --> Params --> Exec",
            "    Env --> Exec",
            "",
            "    %% Trigger Options",
            '    User("User")',
            '    API("API")',
            '    Webhook("Webhook")',
            '    Cron("Scheduled")',
            "    User --> Trigger",
            "    API --> Trigger",
            "    Webhook --> Trigger",
            "    Cron --> Trigger",
            "",
            "    %% Parameters",
            '    subgraph Parameters["Parameters"]',
            "        direction TB",
        ]

        # Add parameters
        for i, arg in enumerate(self.args):
            required = "Required" if arg.required else "Optional"
            arg_desc = f"{arg.name} ({required})"
            if arg.description:
                arg_desc += f"<br/>{escape(arg.description)}"
            if arg.type:
                arg_desc += f"<br/>Type: {escape(arg.type)}"
            if arg.default is not None:
                arg_desc += f"<br/>Default: {escape(str(arg.default))}"
            mermaid.append(f'        Param{i}("{arg_desc}"):::paramClass')

        mermaid.extend(
            [
                "    end",
                "    Parameters --- Params",
                "",
                "    %% Execution",
                '    subgraph Execution["Execution"]',
                "        direction TB",
                f'        Code("Script: {escape(self.content[:50])}...")',
                f'        Type("Type: {escape(self.type.capitalize())}")',
            ]
        )

        if self.image:
            mermaid.append(f'        Image("Docker Image: {escape(self.image)}")')

        mermaid.extend(
            [
                "    end",
                "    Execution --- Exec",
                "",
                "    %% Environment",
                '    subgraph Environment["Environment"]',
                "        direction TB",
            ]
        )

        # Add environment variables
        if self.env:
            env_vars = "<br/>".join(escape(env) for env in self.env)
            mermaid.append(f'        EnvVars("Environment Variables:<br/>{env_vars}"):::envClass')

        # Add secrets
        if self.secrets:
            secrets = "<br/>".join(escape(s) for s in self.secrets)
            mermaid.append(f'        Secrets("Secrets:<br/>{secrets}"):::envClass')

        # Add volumes
        if self.with_volumes:
            volumes = "<br/>".join(f"{escape(v.name)}:{escape(v.path)}" for v in self.with_volumes)
            mermaid.append(f'        Volumes("Volumes:<br/>{volumes}"):::envClass')

        mermaid.extend(
            [
                "    end",
                "    Environment --- Env",
                "",
                "    %% Context Note",
                '    ContextNote("Parameter values can be<br/>fetched from context<br/>based on the trigger")',
                "    ContextNote -.-> Params",
            ]
        )

        return "\n".join(mermaid)

        # # Add parameters with emojis
        # for i, arg in enumerate(self.args):
        #     required = "Required" if arg.required else "Optional"
        #     arg_desc = f"{arg.name}\\n({required})"
        #     if arg.description:
        #         arg_desc += f"\\n{escape(arg.description)}"
        #     if arg.default is not None:
        #         arg_desc += f"\\nDefault: {escape(arg.default)}"
        #     mermaid.append(
        #         f'        Param{i}["{param_emoji} {escape(arg_desc)}"]:::paramClass'
        #     )

        # mermaid.extend(
        #     [
        #         "    end",
        #         "    Parameters --- Params",
        #         "",
        #         "    %% Execution",
        #         "    subgraph Execution[Execution]",
        #         "        direction TB",
        #         f'        Code["{exec_emoji} Script:\\n{escape(self.content[:100])}..."]',
        #         f'        Type["{exec_emoji} Type: {escape(self.type.capitalize())}"]',
        #     ]
        # )

        # if self.image:
        #     mermaid.append(f'        Image["🛠 Docker Image:\\n{escape(self.image)}"]')

        # mermaid.extend(
        #     [
        #         "    end",
        #         "    Execution --- Exec",
        #         "",
        #         "    %% Environment",
        #         "    subgraph Environment[Environment]",
        #         "        direction TB",
        #     ]
        # )

        # # Add environment variables
        # if self.env:
        #     env_vars = "\\n".join(self.env)
        #     mermaid.append(
        #         f'        EnvVars["{env_emoji} Environment Variables:\\n{escape(env_vars)}"]:::envClass'
        #     )

        # # Add secrets
        # if self.secrets:
        #     secrets = "\\n".join(self.secrets)
        #     mermaid.append(
        #         f'        Secrets["{env_emoji} Secrets:\\n{escape(secrets)}"]:::envClass'
        #     )

        # # Add volumes
        # if self.with_volumes:
        #     volumes = "\\n".join(f"{v.name}:{v.path}" for v in self.with_volumes)
        #     mermaid.append(
        #         f'        Volumes["{env_emoji} Volumes:\\n{escape(volumes)}"]:::envClass'
        #     )

        # mermaid.extend(
        #     [
        #         "    end",
        #         "    Environment --- Env",
        #         "",
        #         "    %% Context Note",
        #         f'    ContextNote["{success_emoji} Parameter values can be\\nfetched from context\\nbased on the trigger"]',
        #         "    ContextNote -.-> Params",
        #     ]
        # )

        # return "\n".join(mermaid)
