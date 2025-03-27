"""Base repository interfaces and implementations."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any, Dict
import os
import json
import logging
from pathlib import Path

T = TypeVar('T')
logger = logging.getLogger(__name__)

class Repository(Generic[T], ABC):
    """Abstract base class for all repositories."""
    
    @abstractmethod
    async def save(self, item: T) -> T:
        """Save an item to the repository."""
        pass
        
    @abstractmethod
    async def get_by_id(self, item_id: str) -> Optional[T]:
        """Get an item by its ID."""
        pass
        
    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List items with pagination."""
        pass
        
    @abstractmethod
    async def update(self, item_id: str, item: T) -> Optional[T]:
        """Update an existing item."""
        pass
        
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete an item by its ID."""
        pass


class FileRepository(Repository[Dict[str, Any]]):
    """Simple file-based repository implementation for development/testing."""
    
    def __init__(self, data_dir: Path, collection_name: str):
        """
        Initialize the repository.
        
        Args:
            data_dir: Directory to store data files
            collection_name: Name of the collection (used as filename prefix)
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.file_path = self.data_dir / f"{collection_name}.json"
        self._ensure_data_file()
        
    def _ensure_data_file(self):
        """Create the data file if it doesn't exist."""
        if not self.file_path.exists():
            with open(self.file_path, 'w') as f:
                json.dump([], f)
    
    async def save(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Save an item to the file storage."""
        data = self._load_data()
        
        # Ensure item has an ID
        if 'id' not in item:
            # Generate a simple unique ID
            import uuid
            item['id'] = str(uuid.uuid4())
            
        # Add or update the item
        for i, existing_item in enumerate(data):
            if existing_item.get('id') == item.get('id'):
                data[i] = item
                break
        else:
            data.append(item)
            
        self._save_data(data)
        return item
    
    async def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item by its ID."""
        data = self._load_data()
        for item in data:
            if item.get('id') == item_id:
                return item
        return None
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List items with pagination."""
        data = self._load_data()
        return data[offset:offset+limit]
    
    async def update(self, item_id: str, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing item."""
        data = self._load_data()
        for i, existing_item in enumerate(data):
            if existing_item.get('id') == item_id:
                # Preserve ID
                item['id'] = item_id
                data[i] = item
                self._save_data(data)
                return item
        return None
    
    async def delete(self, item_id: str) -> bool:
        """Delete an item by its ID."""
        data = self._load_data()
        for i, item in enumerate(data):
            if item.get('id') == item_id:
                del data[i]
                self._save_data(data)
                return True
        return False
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """Load data from the file."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading data file: {e}")
            return []
    
    def _save_data(self, data: List[Dict[str, Any]]):
        """Save data to the file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data file: {e}")
