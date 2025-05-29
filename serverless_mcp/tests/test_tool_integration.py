import unittest
import os
import json
from unittest.mock import patch, MagicMock

# Add the parent directory (project root) to the Python path
# to allow imports of serverless_mcp modules if tests are run directly.
import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from serverless_mcp.loader import get_tools
from serverless_mcp.serverless_mcp_tools.base_tool import ServerlessMCPTool, MCP_SERVICE_IMAGE
from serverless_mcp.serverless_mcp_tools.discovery import DiscoveredServerInfo, DiscoveredMCPToolSchema, MCPToolParameterSchema

class TestServerlessMCPIntegration(unittest.TestCase):

    def setUp(self):
        """Set up test environment. Create a dummy config file."""
        self.test_config_dir = os.path.join(os.path.dirname(__file__), "test_config")
        os.makedirs(self.test_config_dir, exist_ok=True)
        self.test_config_path = os.path.join(self.test_config_dir, "servers_to_sync.json")

        self.dummy_server_configs = [
            {
                "id": "dummy_server_1",
                "git_repo_url": "https://example.com/dummy_mcp_server.git",
                "git_branch_or_tag": "main",
                "server_file_path": "server.py",
                "mcp_instance_name": "mcp_app",
                "service_port": 8001,
                "tool_icon_url": "https://example.com/dummy_icon.png"
            }
        ]
        with open(self.test_config_path, 'w') as f:
            json.dump(self.dummy_server_configs, f)

        # Path to loader.py to correctly mock its _CONFIG_FILE_PATH
        self.loader_module_path = "serverless_mcp.loader._CONFIG_FILE_PATH"


    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        if os.path.exists(self.test_config_dir):
            os.rmdir(self.test_config_dir) # Fails if not empty, which is fine for simple cleanup

    @patch("serverless_mcp.serverless_mcp_tools.discovery.discover_mcp_tools_from_config")
    def test_get_tools_loads_and_creates_tools(self, mock_discover):
        """Test that get_tools correctly uses discovery and creates ServerlessMCPTool instances."""
        
        # Mock the output of the discovery process
        mock_discovered_param = MCPToolParameterSchema(name="param1", type="string", required=True, description="Test param")
        mock_discovered_tool = DiscoveredMCPToolSchema(
            name="dummy_mcp_tool", 
            description="A dummy MCP tool", 
            parameters=[mock_discovered_param]
        )
        mock_server_info = DiscoveredServerInfo(
            config=self.dummy_server_configs[0],
            tools=[mock_discovered_tool]
        )
        mock_discover.return_value = [mock_server_info]

        # Patch the _CONFIG_FILE_PATH in loader.py to use our test config
        with patch(self.loader_module_path, self.test_config_path):
            tools = get_tools()

        self.assertEqual(len(tools), 1)
        self.assertIsInstance(tools[0], ServerlessMCPTool)
        mock_discover.assert_called_once_with(self.test_config_path)
        
        created_tool: ServerlessMCPTool = tools[0]
        self.assertEqual(created_tool.name, "dummy_server_1_dummy_mcp_tool")
        self.assertEqual(created_tool.description, "A dummy MCP tool")
        self.assertEqual(len(created_tool.args), 1)
        self.assertEqual(created_tool.args[0].name, "param1")
        self.assertEqual(created_tool.icon_url, "https://example.com/dummy_icon.png")

        # Check service spec
        self.assertEqual(len(created_tool.with_services), 1)
        service_spec = created_tool.with_services[0]
        self.assertEqual(service_spec.name, "mcp-svc-dummy-server-1")
        self.assertEqual(service_spec.image, MCP_SERVICE_IMAGE)
        self.assertIn(8001, service_spec.exposed_ports)
        self.assertEqual(service_spec.env["GIT_REPO_URL"], "https://example.com/dummy_mcp_server.git")
        self.assertEqual(service_spec.env["SERVICE_PORT"], "8001")

    def test_serverless_mcp_tool_init(self):
        """Test the direct instantiation and configuration of ServerlessMCPTool."""
        server_config = {
            "id": "test_server",
            "git_repo_url": "https://git.test/repo.git",
            "git_branch_or_tag": "develop",
            "server_file_path": "app/main.py",
            "mcp_instance_name": "mcp",
            "service_port": 9000,
            "tool_icon_url": "https://my.icon/specific.png"
        }
        tool_schema_dict = {
            "name": "my_cool_tool",
            "description": "Does cool things.",
            "parameters": [
                {"name": "message", "type": "string", "required": True, "description": "A message"},
                {"name": "count", "type": "integer", "required": False, "default": 10}
            ]
        }

        tool = ServerlessMCPTool(mcp_server_config=server_config, tool_schema=tool_schema_dict)

        self.assertEqual(tool.name, "test_server_my_cool_tool")
        self.assertEqual(tool.description, "Does cool things.")
        self.assertEqual(tool.icon_url, "https://my.icon/specific.png")
        self.assertEqual(len(tool.args), 2)
        self.assertEqual(tool.args[0].name, "message")
        self.assertTrue(tool.args[0].required)
        self.assertEqual(tool.args[1].name, "count")
        self.assertFalse(tool.args[1].required)
        self.assertEqual(tool.args[1].default_value, 10)

        # Check generated client script (basic checks)
        self.assertIn("client = Client(server_url='http://mcp-svc-test-server:9000/mcp')", tool.content)
        self.assertIn("mcp_tool_name_to_call = 'my_cool_tool'", tool.content)
        self.assertIn("message = os.getenv('MESSAGE_ARG')", tool.content)
        self.assertIn("count = os.getenv('COUNT_ARG')", tool.content)
        self.assertIn("if count is not None: count = int(count)", tool.content)
        self.assertIn("'message': message, 'count': count", tool.content)

    @patch("serverless_mcp.serverless_mcp_tools.discovery.subprocess.run")
    @patch("serverless_mcp.serverless_mcp_tools.discovery.importlib.util")
    @patch("serverless_mcp.serverless_mcp_tools.discovery.shutil.rmtree")
    def test_discovery_handles_git_clone_failure(self, mock_rmtree, mock_importlib, mock_subprocess_run):
        """Test that discovery logs an error and continues if a git clone fails."""
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "git clone", stderr="Clone failed badly")
        
        # Path to the loader's config file path to patch
        # Needs to point to the actual variable in the loader module
        with patch("serverless_mcp.loader._CONFIG_FILE_PATH", self.test_config_path):
            # discover_mcp_tools_from_config is called by get_tools
            # We are testing the behavior *within* discover_mcp_tools_from_config here implicitly through get_tools.
            # For a more direct test of discover_mcp_tools_from_config, call it directly.
            with self.assertLogs(logger="serverless_mcp.serverless_mcp_tools.discovery", level="ERROR") as log_watcher:
                tools = get_tools() # This will trigger discovery
                self.assertTrue(any("Failed to clone repository" in msg for msg in log_watcher.output))
            self.assertEqual(len(tools), 0) # No tools should be loaded if clone fails

    @patch("discover_exec_script.ensure_k8s_deployment")
    @patch("serverless_mcp.serverless_mcp_tools.discovery.discover_mcp_tools_from_config")
    def test_deploy_mode_skips_tool_generation(self, mock_discover, mock_ensure):
        """Verify that servers in 'deploy' mode trigger ensure_k8s_deployment and do not generate tool defs."""

        # Mock: ensure_k8s_deployment returns True
        mock_ensure.return_value = True

        deploy_cfg = {
            "id": "deploy_only_server",
            "git_repo_url": "https://example.com/repo.git",
            "git_branch_or_tag": "main",
            "server_file_path": "srv.py",
            "mcp_instance_name": "mcp",
            "service_port": 8000,
            "mode": "deploy",
            "docker_image": "repo/image:tag"
        }

        mock_server_info = DiscoveredServerInfo(config=deploy_cfg, tools=[])  # No tools needed in deploy mode
        mock_discover.return_value = [mock_server_info]

        with patch("serverless_mcp.loader.DISCOVER_TOOL_IMAGE_NAME", "test-image"):
            from serverless_mcp.loader import get_tools as loader_get_tools
            tools = loader_get_tools()

        # `tools` only contains the meta-tool definition, not generated tool definitions.
        self.assertEqual(len(tools), 1)
        mock_ensure.assert_not_called()  # ensure_k8s_deployment is called inside discover_exec_script, not loader

    def test_get_parameter_type_conversion(self):
        """Test the _get_parameter_type function for various Python type annotations."""
        from serverless_mcp.serverless_mcp_tools.discovery import _get_parameter_type
        from typing import List, Dict, Any, Optional, Union
        
        # Basic types
        self.assertEqual(_get_parameter_type(str), 'string')
        self.assertEqual(_get_parameter_type(int), 'integer')
        self.assertEqual(_get_parameter_type(float), 'number')
        self.assertEqual(_get_parameter_type(bool), 'boolean')
        self.assertEqual(_get_parameter_type(dict), 'object')
        self.assertEqual(_get_parameter_type(list), 'array')
        
        # Collection types
        self.assertEqual(_get_parameter_type(List[str]), 'array')
        self.assertEqual(_get_parameter_type(Dict[str, int]), 'object')
        
        # Default to string for unknown types
        class CustomType:
            pass
        
        self.assertEqual(_get_parameter_type(CustomType), 'string')
    
    def test_convert_mcp_params_to_kubiya_args(self):
        """Test the _convert_mcp_params_to_kubiya_args function for various MCP parameter schemas."""
        from serverless_mcp.serverless_mcp_tools.base_tool import ServerlessMCPTool
        
        # Create test tool instance
        server_config = {
            "id": "test_server",
            "git_repo_url": "https://test.git",
            "git_branch_or_tag": "main",
            "server_file_path": "server.py",
            "mcp_instance_name": "mcp",
            "service_port": 8000
        }
        
        # Mock a tool instance just to test its _convert_mcp_params_to_kubiya_args method
        tool = ServerlessMCPTool(mcp_server_config=server_config, tool_schema={"name": "test_tool"})
        
        # Test parameters with various types
        mcp_params = [
            {"name": "str_param", "type": "string", "description": "A string", "required": True},
            {"name": "int_param", "type": "integer", "description": "An integer", "required": False, "default": 42},
            {"name": "bool_param", "type": "boolean", "description": "A boolean", "required": True},
            {"name": "num_param", "type": "number", "description": "A float", "required": False, "default": 3.14},
            {"name": "arr_param", "type": "array", "description": "An array", "required": True},
            {"name": "obj_param", "type": "object", "description": "An object", "required": False}
        ]
        
        kubiya_args = tool._convert_mcp_params_to_kubiya_args(mcp_params)
        
        # Verify correct conversion
        self.assertEqual(len(kubiya_args), 6)
        
        # Check string param
        str_arg = next(arg for arg in kubiya_args if arg.name == "str_param")
        self.assertEqual(str_arg.type.name, "STRING")
        self.assertEqual(str_arg.description, "A string")
        self.assertTrue(str_arg.required)
        
        # Check integer param
        int_arg = next(arg for arg in kubiya_args if arg.name == "int_param")
        self.assertEqual(int_arg.type.name, "NUMBER")  # Kubiya uses NUMBER for both int and float
        self.assertEqual(int_arg.description, "An integer")
        self.assertFalse(int_arg.required)
        self.assertEqual(int_arg.default_value, 42)
        
        # Check boolean param
        bool_arg = next(arg for arg in kubiya_args if arg.name == "bool_param")
        self.assertEqual(bool_arg.type.name, "BOOLEAN")
        self.assertTrue(bool_arg.required)
        
        # Check array param
        arr_arg = next(arg for arg in kubiya_args if arg.name == "arr_param")
        self.assertEqual(arr_arg.type.name, "LIST")
        
        # Check object param
        obj_arg = next(arg for arg in kubiya_args if arg.name == "obj_param")
        self.assertEqual(obj_arg.type.name, "JSON_OBJECT")

    def test_missing_config_file(self):
        """Test behavior when config file is missing."""
        nonexistent_path = os.path.join(self.test_config_dir, "nonexistent.json")
        
        from serverless_mcp.serverless_mcp_tools.discovery import discover_mcp_tools_from_config
        
        # Should return empty list without raising exception
        result = discover_mcp_tools_from_config(nonexistent_path)
        self.assertEqual(len(result), 0)
        
        # Test that loader handles this gracefully
        with patch("serverless_mcp.loader._CONFIG_FILE_PATH", nonexistent_path):
            from serverless_mcp.loader import get_tools
            tools = get_tools()
            self.assertEqual(len(tools), 1)  # Still returns meta-tool, even with no config

    # TODO: More tests:
    # - Test discovery logic with a mock file system and mock fastmcp instance
    # - Test the generated client script more thoroughly (e.g., execution with mock fastmcp client)
    # - Test error handling in the client script
    # - Test case where config file contains invalid JSON

if __name__ == '__main__':
    # To run tests and see output, you might need to adjust sys.path or run as a module
    # Example: python -m unittest serverless_mcp.tests.test_tool_integration
    # Ensure serverless_mcp is in PYTHONPATH or current dir is its parent.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main() 