#!/usr/bin/env python3

import sys
import os
import json
import unittest

# Check if the volume mounts are correctly configured
class TestVolumeMounts(unittest.TestCase):

    def setUp(self):
        # Find the correct path to config file - handles both running from root or from serverless_mcp
        if os.path.exists("serverless_mcp/config/servers_to_sync.json"):
            self.config_path = "serverless_mcp/config/servers_to_sync.json"
        elif os.path.exists("config/servers_to_sync.json"):
            self.config_path = "config/servers_to_sync.json"
        else:
            raise FileNotFoundError("Cannot find servers_to_sync.json in either path")
            
        with open(self.config_path, 'r') as f:
            self.configs = json.load(f)

    def test_volume_mounts_in_config(self):
        """Test that volume mounts are correctly configured in servers_to_sync.json"""
        
        print(f"\n=== Testing volume mounts configuration in {self.config_path} ===")
        
        sync_server = None
        deploy_server = None
        
        # Find the servers
        for server in self.configs:
            if server.get("mode") == "sync":
                sync_server = server
            elif server.get("mode") == "deploy":
                deploy_server = server
        
        # Test sync server volume mounts
        self.assertIsNotNone(sync_server, "No server with 'sync' mode found")
        self.assertIn("volumes", sync_server, "Sync server is missing 'volumes' configuration")
        self.assertIsInstance(sync_server["volumes"], list, "Volumes should be a list")
        
        # Count read-only and read-write mounts
        ro_mounts = sum(1 for v in sync_server["volumes"] if ":ro" in v)
        rw_mounts = sum(1 for v in sync_server["volumes"] if ":ro" not in v)
        
        print(f"\nSync server '{sync_server['id']}' has {len(sync_server['volumes'])} volume mounts:")
        print(f"  - {ro_mounts} read-only mounts")
        print(f"  - {rw_mounts} read-write mounts")
        
        for i, volume in enumerate(sync_server["volumes"]):
            parts = volume.split(":")
            host_path = parts[0]
            container_path = parts[1]
            read_only = len(parts) > 2 and parts[2] == "ro"
            
            print(f"  {i+1}. '{host_path}' → '{container_path}' [{'read-only' if read_only else 'read-write'}]")
        
        # Test secrets that have mount paths
        self.assertIn("secrets", sync_server, "Sync server is missing 'secrets' configuration")
        
        mounted_secrets = [s for s in sync_server["secrets"] if isinstance(s, dict) and "mount_path" in s]
        env_secrets = [s for s in sync_server["secrets"] if isinstance(s, str)]
        
        print(f"\nSync server has {len(mounted_secrets)} mounted secrets and {len(env_secrets)} environment secret(s):")
        
        for i, secret in enumerate(mounted_secrets):
            print(f"  {i+1}. Secret '{secret['name']}' mounted at '{secret['mount_path']}'")
        
        for i, secret in enumerate(env_secrets):
            print(f"  {i+1}. Secret '{secret}' injected as environment variables")
        
        # Test deploy server volume mounts
        self.assertIsNotNone(deploy_server, "No server with 'deploy' mode found")
        self.assertIn("volumes", deploy_server, "Deploy server is missing 'volumes' configuration")
        self.assertIsInstance(deploy_server["volumes"], list, "Volumes should be a list")
        
        # Count read-only and read-write mounts
        ro_mounts = sum(1 for v in deploy_server["volumes"] if ":ro" in v)
        rw_mounts = sum(1 for v in deploy_server["volumes"] if ":ro" not in v)
        
        print(f"\nDeploy server '{deploy_server['id']}' has {len(deploy_server['volumes'])} volume mounts:")
        print(f"  - {ro_mounts} read-only mounts")
        print(f"  - {rw_mounts} read-write mounts")
        
        for i, volume in enumerate(deploy_server["volumes"]):
            parts = volume.split(":")
            host_path = parts[0]
            container_path = parts[1]
            read_only = len(parts) > 2 and parts[2] == "ro"
            
            print(f"  {i+1}. '{host_path}' → '{container_path}' [{'read-only' if read_only else 'read-write'}]")
        
        # Test that mounted secrets have the right format
        self.assertIn("secrets", deploy_server, "Deploy server is missing 'secrets' configuration")
        
        mounted_secrets = [s for s in deploy_server["secrets"] if isinstance(s, dict) and "mount_path" in s]
        env_secrets = [s for s in deploy_server["secrets"] if isinstance(s, str)]
        
        print(f"\nDeploy server has {len(mounted_secrets)} mounted secrets and {len(env_secrets)} environment secret(s):")
        
        for i, secret in enumerate(mounted_secrets):
            print(f"  {i+1}. Secret '{secret['name']}' mounted at '{secret['mount_path']}'")
        
        for i, secret in enumerate(env_secrets):
            print(f"  {i+1}. Secret '{secret}' injected as environment variables")
        
        # Check the volume mount format
        for volume in sync_server["volumes"] + deploy_server["volumes"]:
            self.assertRegex(volume, r'^/.+:/.+', "Volume mount must have format '/host/path:/container/path[:ro]'")
            
        # Check that all servers have required properties
        for server in [sync_server, deploy_server]:
            self.assertIn("git_repo_url", server, f"Server '{server['id']}' is missing git_repo_url")
            self.assertIn("git_branch_or_tag", server, f"Server '{server['id']}' is missing git_branch_or_tag")
            self.assertIn("server_file_path", server, f"Server '{server['id']}' is missing server_file_path")
            self.assertIn("mcp_instance_name", server, f"Server '{server['id']}' is missing mcp_instance_name")
            self.assertIn("service_port", server, f"Server '{server['id']}' is missing service_port")
            
            # Check additional deploy-only properties
            if server.get("mode") == "deploy":
                self.assertIn("docker_image", server, f"Deploy server '{server['id']}' is missing docker_image")
                
        print("\nAll tests passed successfully! The volume mounts and secrets configuration is valid.")

if __name__ == "__main__":
    unittest.main() 