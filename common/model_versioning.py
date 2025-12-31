import os
import json
import hashlib
import boto3
from datetime import datetime
from typing import Dict, List, Optional

class ModelVersionManager:
    """Manages model versions with Git-like semantics"""
    
    def __init__(self, bucket_name: str):
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name
        self.versions_prefix = 'model-versions/'
    
    def save_model_version(self, model_state: Dict, metadata: Dict) -> str:
        """Save a model version and return version hash"""
        
        # Create version hash
        model_bytes = json.dumps(model_state, sort_keys=True).encode()
        version_hash = hashlib.sha256(model_bytes).hexdigest()[:12]
        
        # Prepare version metadata
        version_metadata = {
            'version_hash': version_hash,
            'timestamp': datetime.utcnow().isoformat(),
            'parent_version': metadata.get('parent_version'),
            'training_round': metadata.get('round'),
            'accuracy': metadata.get('accuracy'),
            'loss': metadata.get('loss'),
            'privacy_budget_used': metadata.get('epsilon_spent'),
            'num_clients': metadata.get('num_clients'),
            'tags': metadata.get('tags', []),
            'commit_message': metadata.get('message', 'Model update')
        }
        
        # Save model
        model_key = f"{self.versions_prefix}{version_hash}/model.pt"
        metadata_key = f"{self.versions_prefix}{version_hash}/metadata.json"
        
        # Upload to S3
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=model_key,
            Body=json.dumps(model_state)
        )
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=metadata_key,
            Body=json.dumps(version_metadata)
        )
        
        # Update version index
        self._update_version_index(version_hash, version_metadata)
        
        return version_hash
    
    def get_model_version(self, version_hash: str) -> Dict:
        """Retrieve a specific model version"""
        
        model_key = f"{self.versions_prefix}{version_hash}/model.pt"
        metadata_key = f"{self.versions_prefix}{version_hash}/metadata.json"
        
        # Download from S3
        model_obj = self.s3.get_object(Bucket=self.bucket_name, Key=model_key)
        model_state = json.loads(model_obj['Body'].read())
        
        metadata_obj = self.s3.get_object(Bucket=self.bucket_name, Key=metadata_key)
        metadata = json.loads(metadata_obj['Body'].read())
        
        return {
            'model_state': model_state,
            'metadata': metadata
        }
    
    def list_versions(self, limit: int = 20) -> List[Dict]:
        """List recent model versions"""
        
        # Get version index
        try:
            index_obj = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=f"{self.versions_prefix}index.json"
            )
            index = json.loads(index_obj['Body'].read())
            
            # Sort by timestamp and return latest
            versions = sorted(
                index['versions'],
                key=lambda x: x['timestamp'],
                reverse=True
            )[:limit]
            
            return versions
        except:
            return []
    
    def tag_version(self, version_hash: str, tag: str):
        """Tag a model version (e.g., 'production', 'staging')"""
        
        # Get current metadata
        metadata_key = f"{self.versions_prefix}{version_hash}/metadata.json"
        metadata_obj = self.s3.get_object(Bucket=self.bucket_name, Key=metadata_key)
        metadata = json.loads(metadata_obj['Body'].read())
        
        # Add tag
        if 'tags' not in metadata:
            metadata['tags'] = []
        if tag not in metadata['tags']:
            metadata['tags'].append(tag)
        
        # Save updated metadata
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata)
        )
        
        # Update tag index
        self._update_tag_index(tag, version_hash)
    
    def get_version_by_tag(self, tag: str) -> Optional[Dict]:
        """Get model version by tag (e.g., get 'production' model)"""
        
        try:
            tag_obj = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=f"{self.versions_prefix}tags/{tag}.json"
            )
            tag_data = json.loads(tag_obj['Body'].read())
            
            return self.get_model_version(tag_data['version_hash'])
        except:
            return None
    
    def rollback(self, version_hash: str):
        """Rollback to a specific model version"""
        
        # Tag current production as 'previous'
        current_prod = self.get_version_by_tag('production')
        if current_prod:
            self.tag_version(
                current_prod['metadata']['version_hash'],
                'previous-production'
            )
        
        # Tag specified version as production
        self.tag_version(version_hash, 'production')
        
        return version_hash
    
    def _update_version_index(self, version_hash: str, metadata: Dict):
        """Update the version index"""
        
        # Get current index
        try:
            index_obj = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=f"{self.versions_prefix}index.json"
            )
            index = json.loads(index_obj['Body'].read())
        except:
            index = {'versions': []}
        
        # Add new version
        index['versions'].append({
            'version_hash': version_hash,
            'timestamp': metadata['timestamp'],
            'accuracy': metadata.get('accuracy'),
            'tags': metadata.get('tags', [])
        })
        
        # Save updated index
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.versions_prefix}index.json",
            Body=json.dumps(index)
        )
    
    def _update_tag_index(self, tag: str, version_hash: str):
        """Update tag to version mapping"""
        
        tag_data = {
            'tag': tag,
            'version_hash': version_hash,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.versions_prefix}tags/{tag}.json",
            Body=json.dumps(tag_data)
        )