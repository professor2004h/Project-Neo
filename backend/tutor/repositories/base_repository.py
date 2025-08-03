"""
Base repository class for database operations
"""
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from services.supabase import DBConnection
from utils.logger import logger


class BaseRepository(ABC):
    """Base repository class with common database operations"""
    
    def __init__(self, db: DBConnection, table_name: str):
        self.db = db
        self.table_name = table_name
    
    async def get_client(self):
        """Get the database client"""
        return await self.db.client
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).insert(data).execute()
            
            if result.data:
                logger.info(f"Created record in {self.table_name}")
                return result.data[0]
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            logger.error(f"Error creating record in {self.table_name}: {str(e)}")
            raise
    
    async def get_by_id(self, record_id: str, id_column: str = "id") -> Optional[Dict[str, Any]]:
        """Get a record by ID"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq(id_column, record_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting record from {self.table_name}: {str(e)}")
            raise
    
    async def update(self, record_id: str, data: Dict[str, Any], id_column: str = "id") -> Dict[str, Any]:
        """Update a record"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).update(data).eq(id_column, record_id).execute()
            
            if result.data:
                logger.info(f"Updated record in {self.table_name}")
                return result.data[0]
            else:
                raise Exception("No data returned from update operation")
                
        except Exception as e:
            logger.error(f"Error updating record in {self.table_name}: {str(e)}")
            raise
    
    async def delete(self, record_id: str, id_column: str = "id") -> bool:
        """Delete a record"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).delete().eq(id_column, record_id).execute()
            
            logger.info(f"Deleted record from {self.table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting record from {self.table_name}: {str(e)}")
            raise
    
    async def list_all(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all records with optional filters"""
        try:
            client = await self.get_client()
            query = client.table(self.table_name).select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            if limit:
                query = query.limit(limit)
            
            result = await query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error listing records from {self.table_name}: {str(e)}")
            raise