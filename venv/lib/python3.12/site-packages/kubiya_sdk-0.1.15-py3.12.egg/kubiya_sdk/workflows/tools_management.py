from pydantic import BaseModel

from kubiya_sdk.utils.logging_config import get_logger

logger = get_logger("kubiya_sdk.ToolsManagement")


class ToolsManagement:
    def __init__(self):
        self.registry = {}
        logger.info("Initialized ToolsManagement.")

    def load_tools(self, source_url: str):
        """
        Load tools from a given source URL.
        This should be done only once per source.
        """
        if source_url not in self.registry:
            # Simulated loading tools from a source
            self.registry[source_url] = {
                #  "example_tool": ExampleTool()
            }
            logger.info(f"Loaded tools from source: {source_url}")
        else:
            logger.debug(f"Tools already loaded from source: {source_url}")

    def get_tool(self, source_url: str, tool_name: str):
        """
        Retrieve a tool by name from a source URL.
        """
        logger.debug(f"Getting tool `{tool_name}` from source `{source_url}`.")
        self.load_tools(source_url)

        tool = self.registry[source_url].get(tool_name)
        if not tool:
            logger.error(f"Tool `{tool_name}` not found in `{source_url}`.")
            raise ValueError(f"Tool `{tool_name}` not found in `{source_url}`.")

        logger.info(f"Successfully retrieved tool `{tool_name}` from `{source_url}`.")
        return tool

    def list_tools(self, source_url: str):
        """
        List all available tools in the specified source.
        """
        logger.debug(f"Listing tools from source `{source_url}`.")
        self.load_tools(source_url)
        tools = list(self.registry[source_url].keys())
        logger.info(f"Available tools in `{source_url}`: {tools}")
        return tools

    def describe_tool_schema(self, source_url: str, tool_name: str):
        """
        Get the input schema for a specified tool.
        """
        logger.debug(f"Describing tool schema for `{tool_name}` from `{source_url}`.")
        tool = self.get_tool(source_url, tool_name)
        schema = tool.get_input_schema()
        logger.info(f"Tool schema for `{tool_name}`: {schema}")
        return schema

    def execute_tool(
        self,
        source_url: str,
        tool_name: str,
        parameters: BaseModel,
        async_flag: bool = False,
    ):
        """
        Execute a tool directly from the registry.

        :param source_url: URL of the source where the tool is located.
        :param tool_name: The name of the tool to execute.
        :param parameters: A Pydantic model instance containing the tool parameters.
        :param async_flag: Whether to execute the tool asynchronously.
        :return: The result of the tool execution.
        """
        logger.debug(f"Executing tool `{tool_name}` from `{source_url}` with params {parameters}. Async: {async_flag}")
        tool = self.get_tool(source_url, tool_name)

        if async_flag:
            result = tool.execute_async(parameters)
        else:
            result = tool.execute(parameters)

        logger.info(f"Execution result for `{tool_name}`: {result}")
        return result


tools_management = ToolsManagement()
