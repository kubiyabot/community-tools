from dataclasses import dataclass
from typing import List, Optional

@dataclass
class WorkspaceConfig:
    workspace_name: str
    region: str
    storage_account_name: str
    container_name: str
    resource_group_name: str
    managed_services_cmk_key_vault_key_id: Optional[str] = None
    managed_disk_cmk_key_vault_key_id: Optional[str] = None
    infrastructure_encryption_enabled: bool = False
    no_public_ip: bool = False
    enable_vnet: bool = False
    virtual_network_id: Optional[str] = None
    private_subnet_name: Optional[str] = None
    public_subnet_name: Optional[str] = None
    public_subnet_network_security_group_association_id: Optional[str] = None
    private_subnet_network_security_group_association_id: Optional[str] = None
    security_profile_enabled: bool = False
    enhanced_monitoring_enabled: bool = False
    automatic_update: bool = False
    restart_no_updates: bool = False
    day_of_week: Optional[str] = None
    frequency: Optional[str] = None
    hours: str = "1"
    minutes: str = "0"
    address_space: List[str] = ["10.0.0.0/16"]
    address_prefixes_public: List[str] = ["10.0.2.0/24"]
    address_prefixes_private: List[str] = ["10.0.1.0/24"]