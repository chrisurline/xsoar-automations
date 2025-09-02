
"""
XSIAM incident + alert copy script
copies random incidents and their child alerts from production to dev tenant
"""

import requests
import json
import random
import logging
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import argparse
import sys

# logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('xsiam_copy.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class XSIAMClient:
    """Client for interacting with XSIAM API"""
    
    def __init__(self, base_url: str, api_key: str, api_key_id: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_key_id = api_key_id
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'{api_key_id}:{api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_incidents(self, limit: int = 100, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch incidents from the last N days"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            params = {
                'limit': limit,
                'sort': 'created_time:desc',
                'filter': f'created_time:gte:{int(start_date.timestamp() * 1000)}'
            }
            
            response = self.session.get(
                f'{self.base_url}/public_api/v1/incidents/get_incidents',
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            incidents = data.get('reply', {}).get('incidents', [])
            logger.info(f"Retrieved {len(incidents)} incidents")
            return incidents
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch incidents: {e}")
            return []
    
    def get_incident_alerts(self, incident_id: str) -> List[Dict[str, Any]]:
        """Fetch alerts associated with an incident"""
        try:
            params = {
                'incident_id': incident_id
            }
            
            response = self.session.get(
                f'{self.base_url}/public_api/v1/alerts/get_alerts_by_filter',
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            alerts = data.get('reply', {}).get('alerts', [])
            logger.info(f"Retrieved {len(alerts)} alerts for incident {incident_id}")
            return alerts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch alerts for incident {incident_id}: {e}")
            return []
    
    def create_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Create a new alert in the target tenant"""
        try:
            # Remove fields that shouldn't be copied
            clean_alert = self._clean_alert_data(alert_data)
            
            response = self.session.post(
                f'{self.base_url}/public_api/v1/alerts/insert_parsed_alerts',
                json={'alerts': [clean_alert]}
            )
            response.raise_for_status()
            
            logger.info(f"Successfully created alert: {clean_alert.get('alert_id', 'unknown')}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create alert: {e}")
            return False
    
    def _clean_alert_data(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean alert data for copying to new tenant"""
        # Fields to remove (system-generated or tenant-specific)
        fields_to_remove = [
            'tenant_id',
            'alert_id',  # Will get new ID in target tenant
            'creation_time',  # Will be set by target tenant
            'detection_timestamp',
            'modification_time',
            'starred',
            'manual_severity',
            'assigned_user_mail',
            'assigned_user_pretty_name',
            'status',
            'resolve_comment',
            'notes',
            'original_tags'
        ]
        
        # Create clean copy
        clean_alert = {}
        for key, value in alert_data.items():
            if key not in fields_to_remove:
                clean_alert[key] = value
        
        # Add dev tenant identifier
        clean_alert['description'] = f"[DEV COPY] {clean_alert.get('description', '')}"
        clean_alert['alert_name'] = f"[DEV] {clean_alert.get('alert_name', '')}"
        
        return clean_alert

class IncidentCopyJob:
    """Main job class for copying incidents and alerts"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize source and target clients
        self.source_client = XSIAMClient(
            config['source']['base_url'],
            config['source']['api_key'],
            config['source']['api_key_id']
        )
        
        self.target_client = XSIAMClient(
            config['target']['base_url'],
            config['target']['api_key'],
            config['target']['api_key_id']
        )
    
    def run(self):
        """Execute the incident copy job"""
        logger.info("Starting incident copy job")
        
        try:
            # Get incidents from source
            incidents = self.source_client.get_incidents(
                limit=self.config.get('max_incidents', 100),
                days_back=self.config.get('days_back', 7)
            )
            
            if not incidents:
                logger.warning("No incidents found to copy")
                return
            
            # Select random subset
            num_to_copy = min(
                self.config.get('incidents_to_copy', 10),
                len(incidents)
            )
            selected_incidents = random.sample(incidents, num_to_copy)
            logger.info(f"Selected {len(selected_incidents)} incidents to copy")
            
            # Process each incident
            total_alerts_copied = 0
            for incident in selected_incidents:
                incident_id = incident.get('incident_id')
                logger.info(f"Processing incident: {incident_id}")
                
                # Get alerts for this incident
                alerts = self.source_client.get_incident_alerts(incident_id)
                
                if not alerts:
                    logger.warning(f"No alerts found for incident {incident_id}")
                    continue
                
                # Copy alerts to target tenant
                copied_count = 0
                for alert in alerts:
                    if self.target_client.create_alert(alert):
                        copied_count += 1
                        # Add delay to avoid rate limiting
                        time.sleep(0.5)
                
                logger.info(f"Copied {copied_count}/{len(alerts)} alerts from incident {incident_id}")
                total_alerts_copied += copied_count
            
            logger.info(f"Job completed. Total alerts copied: {total_alerts_copied}")
            
        except Exception as e:
            logger.error(f"Job failed with error: {e}")
            raise

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)

def create_sample_config():
    """Create a sample configuration file"""
    sample_config = {
        "source": {
            "base_url": "https://your-prod-tenant.xdr.us.paloaltonetworks.com",
            "api_key": "your_source_api_key",
            "api_key_id": "your_source_api_key_id"
        },
        "target": {
            "base_url": "https://your-dev-tenant.xdr.us.paloaltonetworks.com",
            "api_key": "your_target_api_key",
            "api_key_id": "your_target_api_key_id"
        },
        "max_incidents": 100,
        "incidents_to_copy": 10,
        "days_back": 7
    }
    
    with open('config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("Sample configuration file 'config.json' created.")
    print("Please update it with your actual XSIAM tenant details and API keys.")

def main():
    parser = argparse.ArgumentParser(description='Copy XSIAM incidents and alerts to dev tenant')
    parser.add_argument('--config', '-c', default='config.json', 
                       help='Configuration file path (default: config.json)')
    parser.add_argument('--create-config', action='store_true',
                       help='Create a sample configuration file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run without actually creating alerts in target tenant')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_sample_config()
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Validate required configuration
    required_fields = [
        'source.base_url', 'source.api_key', 'source.api_key_id',
        'target.base_url', 'target.api_key', 'target.api_key_id'
    ]
    
    for field in required_fields:
        keys = field.split('.')
        value = config
        for key in keys:
            value = value.get(key, {})
        if not value:
            logger.error(f"Missing required configuration: {field}")
            sys.exit(1)
    
    # Run the job
    try:
        job = IncidentCopyJob(config)
        job.run()
    except KeyboardInterrupt:
        logger.info("Job interrupted by user")
    except Exception as e:
        logger.error(f"Job failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()