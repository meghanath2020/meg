"""
Configuration module for ServiceNow instances
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class InstanceConfig:
    """Configuration for a single ServiceNow instance"""

    def __init__(self, instance_name: str, config_dict: dict):
        self.instance_name = instance_name
        self.base_url = config_dict.get('base_url', '')
        self.extraction_method = config_dict.get('extraction_method', 'jsonv2')  # jsonv2 or rest_api
        self.use_parent_groups = config_dict.get('use_parent_groups', True)
        self.assignment_groups_file = config_dict.get('assignment_groups_file', '')
        self.ticket_types = config_dict.get('ticket_types', [])
        self.output_folder = config_dict.get('output_folder', f'output/{instance_name}')
        self.last_extraction_file = os.path.join(self.output_folder, '.last_extraction.json')

    def get_query_field(self) -> str:
        """Get the field name for querying assignment groups"""
        if self.use_parent_groups:
            return "assignment_group.parent.nameIN"
        else:
            return "assignment_groupIN"

    def get_last_extraction_time(self) -> Optional[datetime]:
        """Get the last extraction datetime"""
        if os.path.exists(self.last_extraction_file):
            try:
                with open(self.last_extraction_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data.get('last_extraction'))
            except Exception as e:
                print(f"Error reading last extraction time: {e}")
                return None
        return None

    def save_extraction_time(self, extraction_time: datetime):
        """Save the extraction datetime"""
        os.makedirs(os.path.dirname(self.last_extraction_file), exist_ok=True)
        with open(self.last_extraction_file, 'w') as f:
            json.dump({'last_extraction': extraction_time.isoformat()}, f)


class ServiceNowConfig:
    """Main configuration class for all ServiceNow instances"""

    # URL templates for different ticket types
    JSONV2_URL_TEMPLATES = {
        'incident': '{base_url}/incident_list.do?JSONv2&sysparm_query={query}&displayvalue=true',
        'sc_task': '{base_url}/sc_task.do?JSONv2&sysparm_query={query}&displayvalue=true',
        'incident_task': '{base_url}/incident_task_list.do?JSONv2&sysparm_query={query}&displayvalue=true',
        'problem': '{base_url}/problem_list.do?JSONv2&sysparm_query={query}&displayvalue=true'
    }

    # REST API endpoints
    REST_API_TEMPLATES = {
        'incident': '{base_url}/api/now/table/incident?sysparm_query={query}&sysparm_display_value=true',
        'sc_task': '{base_url}/api/now/table/sc_task?sysparm_query={query}&sysparm_display_value=true',
        'incident_task': '{base_url}/api/now/table/incident_task?sysparm_query={query}&sysparm_display_value=true',
        'problem': '{base_url}/api/now/table/problem?sysparm_query={query}&sysparm_display_value=true'
    }

    def __init__(self, config_file: str = 'config/instances.json'):
        self.config_file = config_file
        self.instances: Dict[str, InstanceConfig] = {}
        self.load_config()

    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
                for instance_name, instance_data in config_data.items():
                    self.instances[instance_name] = InstanceConfig(instance_name, instance_data)
        else:
            # Create default configuration
            self.create_default_config()

    def create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "instance1": {
                "base_url": "https://instance1.service-now.com",
                "extraction_method": "jsonv2",
                "use_parent_groups": True,
                "assignment_groups_file": "assignment_groups/instance1_groups.xlsx",
                "ticket_types": ["incident", "sc_task", "incident_task", "problem"],
                "output_folder": "output/instance1"
            },
            "instance2": {
                "base_url": "https://instance2.service-now.com",
                "extraction_method": "jsonv2",
                "use_parent_groups": True,
                "assignment_groups_file": "assignment_groups/instance2_groups.xlsx",
                "ticket_types": ["incident", "sc_task"],
                "output_folder": "output/instance2"
            },
            "instance3": {
                "base_url": "https://instance3.service-now.com",
                "extraction_method": "rest_api",
                "use_parent_groups": False,
                "assignment_groups_file": "assignment_groups/instance3_groups.xlsx",
                "ticket_types": ["incident"],
                "output_folder": "output/instance3"
            }
        }

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        # Reload config
        self.load_config()

    def get_instance(self, instance_name: str) -> Optional[InstanceConfig]:
        """Get configuration for a specific instance"""
        return self.instances.get(instance_name)

    def get_all_instances(self) -> List[str]:
        """Get list of all instance names"""
        return list(self.instances.keys())

    def build_url(self, instance_name: str, ticket_type: str, query: str) -> str:
        """Build complete URL for data extraction"""
        instance = self.get_instance(instance_name)
        if not instance:
            raise ValueError(f"Instance {instance_name} not found")

        if instance.extraction_method == 'jsonv2':
            template = self.JSONV2_URL_TEMPLATES.get(ticket_type)
        else:
            template = self.REST_API_TEMPLATES.get(ticket_type)

        if not template:
            raise ValueError(f"Unknown ticket type: {ticket_type}")

        return template.format(base_url=instance.base_url, query=query)
