from kubiya_sdk.tools import FileSpec

COMMON_ENV = [
    "GITHUB_TOKEN",
]

COMMON_FILES = [
    FileSpec(source="~/.config/gh/config.yml", destination="/root/.config/gh/config.yml"),
]