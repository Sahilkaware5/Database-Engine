#!/usr/bin/env python3
"""
Database Engine Setup Script
Installs required Python dependencies and initializes the database
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages"""
    requirements = [
        'flask>=2.3.0',
        'flask-cors>=4.0.0',
        'pytest>=7.0.0'
    ]
    
    print("Installing Python dependencies...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = ['database', 'logs', 'backups']
    
    print("\nCreating directories...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created {directory}/ directory")

def initialize_database():
    """Initialize the database with sample data"""
    print("\nInitializing database...")
    
    try:
        from storage_engine import DatabaseEngine, Column, DataType
        
        # Create database engine
        db = DatabaseEngine()
        
        # Create sample tables
        if 'users' not in db.tables:
            user_columns = [
                Column("id", DataType.INT, primary_key=True),
                Column("name", DataType.VARCHAR, size=50, nullable=False),
                Column("email", DataType.VARCHAR, size=100),
                Column("age", DataType.INT, default_value=0)
            ]
            db.create_table("users", user_columns)
            
            # Insert sample data
            sample_users = [
                {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25},
                {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35},
                {"id": 4, "name": "Alice Brown", "email": "alice@example.com", "age": 28},
                {"id": 5, "name": "Charlie Wilson", "email": "charlie@example.com", "age": 42}
            ]
            
            for user in sample_users:
                db.insert_into("users", user)
            
            print("✓ Created 'users' table with sample data")
        
        if 'products' not in db.tables:
            product_columns = [
                Column("id", DataType.INT, primary_key=True),
                Column("name", DataType.VARCHAR, size=100, nullable=False),
                Column("price", DataType.FLOAT),
                Column("category", DataType.VARCHAR, size=50),
                Column("in_stock", DataType.BOOLEAN, default_value=True)
            ]
            db.create_table("products", product_columns)
            
            # Insert sample data
            sample_products = [
                {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics", "in_stock": True},
                {"id": 2, "name": "Book", "price": 19.99, "category": "Education", "in_stock": True},
                {"id": 3, "name": "Coffee Mug", "price": 12.50, "category": "Kitchen", "in_stock": False},
                {"id": 4, "name": "Smartphone", "price": 699.99, "category": "Electronics", "in_stock": True},
                {"id": 5, "name": "Desk Chair", "price": 149.99, "category": "Furniture", "in_stock": True}
            ]
            
            for product in sample_products:
                db.insert_into("products", product)
            
            print("✓ Created 'products' table with sample data")
        
        if 'orders' not in db.tables:
            order_columns = [
                Column("id", DataType.INT, primary_key=True),
                Column("user_id", DataType.INT, nullable=False),
                Column("product_id", DataType.INT, nullable=False),
                Column("quantity", DataType.INT, default_value=1),
                Column("total", DataType.FLOAT)
            ]
            db.create_table("orders", order_columns)
            
            # Insert sample data
            sample_orders = [
                {"id": 1, "user_id": 1, "product_id": 1, "quantity": 1, "total": 999.99},
                {"id": 2, "user_id": 2, "product_id": 2, "quantity": 2, "total": 39.98},
                {"id": 3, "user_id": 3, "product_id": 4, "quantity": 1, "total": 699.99},
                {"id": 4, "user_id": 1, "product_id": 5, "quantity": 1, "total": 149.99}
            ]
            
            for order in sample_orders:
                db.insert_into("orders", order)
            
            print("✓ Created 'orders' table with sample data")
        
        # Create some indexes
        try:
            db.create_index("users", "email", "idx_users_email")
            print("✓ Created index on users.email")
        except:
            pass  # Index might already exist
        
        try:
            db.create_index("products", "category", "idx_products_category")
            print("✓ Created index on products.category")
        except:
            pass  # Index might already exist
        
        print("✓ Database initialization completed")
        return True
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🗄️  Database Engine Setup")
    print("=" * 50)
    
    # Install dependencies
    if not install_requirements():
        print("\n❌ Setup failed during dependency installation")
        return False
    
    # Create directories
    create_directories()
    
    # Initialize database
    if not initialize_database():
        print("\n❌ Setup failed during database initialization")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the Python API server:")
    print("   python scripts/api_server.py")
    print("\n2. Start the TypeScript frontend:")
    print("   npm run dev")
    print("\n3. Open http://localhost:3000 in your browser")
    print("\nThe API will be available at http://localhost:5000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
