import os
import json
import pickle
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DataType(Enum):
    INT = "INT"
    VARCHAR = "VARCHAR"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"

@dataclass
class Column:
    name: str
    data_type: DataType
    size: Optional[int] = None
    primary_key: bool = False
    nullable: bool = True
    default_value: Any = None

class Page:
    """Fixed-size page (4KB) for storing data"""
    PAGE_SIZE = 4096
    
    def __init__(self, page_id: int = 0):
        self.page_id = page_id
        self.records = []
        self.free_space = self.PAGE_SIZE
        self.is_dirty = False
    
    def can_fit_record(self, record_size: int) -> bool:
        return self.free_space >= record_size + 50  # 50 bytes overhead
    
    def insert_record(self, record: Dict[str, Any]) -> bool:
        record_data = json.dumps(record, default=str)
        record_size = len(record_data.encode('utf-8'))
        
        if not self.can_fit_record(record_size):
            return False
        
        self.records.append(record)
        self.free_space -= record_size + 50
        self.is_dirty = True
        return True
    
    def get_records(self) -> List[Dict[str, Any]]:
        return self.records.copy()

class Table:
    """Represents a database table"""
    
    def __init__(self, name: str, columns: List[Column]):
        self.name = name
        self.columns = {col.name: col for col in columns}
        self.column_order = [col.name for col in columns]
        self.pages: List[Page] = []
        self.indexes: Dict[str, Dict] = {}
        self.primary_key = None
        
        # Find primary key
        for col in columns:
            if col.primary_key:
                self.primary_key = col.name
                break
    
    def validate_record(self, record: Dict[str, Any]) -> bool:
        """Validate record against table schema"""
        for col_name, column in self.columns.items():
            value = record.get(col_name)
            
            # Check nullable
            if value is None and not column.nullable:
                raise ValueError(f"Column {col_name} cannot be null")
            
            # Check data type
            if value is not None:
                if column.data_type == DataType.INT and not isinstance(value, int):
                    try:
                        record[col_name] = int(value)
                    except ValueError:
                        raise ValueError(f"Invalid integer value for {col_name}")
                
                elif column.data_type == DataType.VARCHAR:
                    if column.size and len(str(value)) > column.size:
                        raise ValueError(f"Value too long for {col_name}")
                    record[col_name] = str(value)
                
                elif column.data_type == DataType.FLOAT:
                    try:
                        record[col_name] = float(value)
                    except ValueError:
                        raise ValueError(f"Invalid float value for {col_name}")
        
        return True
    
    def insert(self, record: Dict[str, Any]) -> bool:
        """Insert a record into the table"""
        # Add missing columns with default values
        for col_name, column in self.columns.items():
            if col_name not in record:
                record[col_name] = column.default_value
        
        # Validate record
        self.validate_record(record)
        
        # Try to insert into existing pages
        for page in self.pages:
            if page.insert_record(record):
                self.update_indexes(record)
                return True
        
        # Create new page if needed
        new_page = Page(len(self.pages))
        if new_page.insert_record(record):
            self.pages.append(new_page)
            self.update_indexes(record)
            return True
        
        return False
    
    def select(self, where_clause: Optional[Dict] = None, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Select records from the table"""
        results = []
        
        for page in self.pages:
            for record in page.get_records():
                # Apply WHERE clause
                if where_clause and not self.evaluate_where_clause(record, where_clause):
                    continue
                
                # Project columns
                if columns:
                    projected_record = {col: record.get(col) for col in columns if col in record}
                    results.append(projected_record)
                else:
                    results.append(record.copy())
        
        return results
    
    def evaluate_where_clause(self, record: Dict[str, Any], where_clause: Dict) -> bool:
        """Evaluate WHERE clause against a record"""
        column = where_clause.get('column')
        operator = where_clause.get('operator')
        value = where_clause.get('value')
        
        if column not in record:
            return False
        
        record_value = record[column]
        
        if operator == '=':
            return record_value == value
        elif operator == '!=':
            return record_value != value
        elif operator == '>':
            return record_value > value
        elif operator == '<':
            return record_value < value
        elif operator == '>=':
            return record_value >= value
        elif operator == '<=':
            return record_value <= value
        elif operator == 'LIKE':
            return str(value).replace('%', '.*') in str(record_value)
        
        return False
    
    def update_indexes(self, record: Dict[str, Any]):
        """Update indexes when a record is inserted"""
        for index_name, index_data in self.indexes.items():
            column_name = index_data['column']
            if column_name in record:
                if 'values' not in index_data:
                    index_data['values'] = {}
                index_data['values'][record[column_name]] = record

class DatabaseEngine:
    """Main database engine"""
    
    def __init__(self, db_path: str = "./database"):
        self.db_path = db_path
        self.tables: Dict[str, Table] = {}
        os.makedirs(db_path, exist_ok=True)
        self.load_metadata()
    
    def create_table(self, table_name: str, columns: List[Column]) -> bool:
        """Create a new table"""
        if table_name in self.tables:
            raise ValueError(f"Table {table_name} already exists")
        
        table = Table(table_name, columns)
        self.tables[table_name] = table
        self.save_metadata()
        return True
    
    def drop_table(self, table_name: str) -> bool:
        """Drop a table"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        del self.tables[table_name]
        self.save_metadata()
        
        # Remove table file
        table_file = os.path.join(self.db_path, f"{table_name}.tbl")
        if os.path.exists(table_file):
            os.remove(table_file)
        
        return True
    
    def insert_into(self, table_name: str, record: Dict[str, Any]) -> bool:
        """Insert record into table"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        result = self.tables[table_name].insert(record)
        if result:
            self.save_table(table_name)
        return result
    
    def select_from(self, table_name: str, where_clause: Optional[Dict] = None, 
                   columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Select records from table"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        return self.tables[table_name].select(where_clause, columns)
    
    def create_index(self, table_name: str, column_name: str, index_name: str) -> bool:
        """Create an index on a column"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        table = self.tables[table_name]
        if column_name not in table.columns:
            raise ValueError(f"Column {column_name} does not exist")
        
        table.indexes[index_name] = {
            'column': column_name,
            'type': 'btree',
            'values': {}
        }
        
        # Build index from existing data
        for page in table.pages:
            for record in page.get_records():
                if column_name in record:
                    table.indexes[index_name]['values'][record[column_name]] = record
        
        self.save_table(table_name)
        return True
    
    def save_table(self, table_name: str):
        """Save table to disk"""
        table_file = os.path.join(self.db_path, f"{table_name}.tbl")
        with open(table_file, 'wb') as f:
            pickle.dump(self.tables[table_name], f)
    
    def load_table(self, table_name: str) -> Optional[Table]:
        """Load table from disk"""
        table_file = os.path.join(self.db_path, f"{table_name}.tbl")
        if os.path.exists(table_file):
            with open(table_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def save_metadata(self):
        """Save database metadata"""
        metadata = {
            'tables': {}
        }
        
        for table_name, table in self.tables.items():
            metadata['tables'][table_name] = {
                'columns': [
                    {
                        'name': col.name,
                        'data_type': col.data_type.value,
                        'size': col.size,
                        'primary_key': col.primary_key,
                        'nullable': col.nullable,
                        'default_value': col.default_value
                    }
                    for col in table.columns.values()
                ],
                'indexes': list(table.indexes.keys())
            }
        
        metadata_file = os.path.join(self.db_path, 'metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_metadata(self):
        """Load database metadata"""
        metadata_file = os.path.join(self.db_path, 'metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            for table_name, table_info in metadata['tables'].items():
                columns = []
                for col_info in table_info['columns']:
                    columns.append(Column(
                        name=col_info['name'],
                        data_type=DataType(col_info['data_type']),
                        size=col_info.get('size'),
                        primary_key=col_info.get('primary_key', False),
                        nullable=col_info.get('nullable', True),
                        default_value=col_info.get('default_value')
                    ))
                
                table = Table(table_name, columns)
                
                # Load table data
                loaded_table = self.load_table(table_name)
                if loaded_table:
                    table.pages = loaded_table.pages
                    table.indexes = loaded_table.indexes
                
                self.tables[table_name] = table
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get table information"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        table = self.tables[table_name]
        total_records = sum(len(page.records) for page in table.pages)
        
        return {
            'name': table_name,
            'columns': [
                {
                    'name': col.name,
                    'type': col.data_type.value,
                    'size': col.size,
                    'primary_key': col.primary_key,
                    'nullable': col.nullable
                }
                for col in table.columns.values()
            ],
            'total_records': total_records,
            'total_pages': len(table.pages),
            'indexes': list(table.indexes.keys())
        }
    
    def list_tables(self) -> List[str]:
        """List all tables in the database"""
        return list(self.tables.keys())

# Example usage and testing
if __name__ == "__main__":
    # Create database engine
    db = DatabaseEngine()
    
    # Create a users table
    user_columns = [
        Column("id", DataType.INT, primary_key=True),
        Column("name", DataType.VARCHAR, size=50, nullable=False),
        Column("email", DataType.VARCHAR, size=100),
        Column("age", DataType.INT, default_value=0)
    ]
    
    db.create_table("users", user_columns)
    
    # Insert some data
    db.insert_into("users", {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30})
    db.insert_into("users", {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25})
    db.insert_into("users", {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35})
    
    # Create an index
    db.create_index("users", "email", "idx_email")
    
    # Query data
    all_users = db.select_from("users")
    print("All users:", all_users)
    
    # Query with WHERE clause
    young_users = db.select_from("users", where_clause={"column": "age", "operator": "<", "value": 30})
    print("Young users:", young_users)
    
    # Get table info
    table_info = db.get_table_info("users")
    print("Table info:", table_info)
    
    print("Database engine test completed successfully!")
