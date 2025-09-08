#!/usr/bin/env python3
"""
Database Engine Server Startup Script
Ensures proper initialization and starts the Flask server
"""

import os
import sys
import time
import subprocess
import socket
from storage_engine import DatabaseEngine, Column, DataType

def check_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def check_dependencies():
    """Check if required packages are installed"""
    missing_packages = []
    
    try:
        import flask
        print("✓ Flask is available")
    except ImportError:
        missing_packages.append("flask")
    
    try:
        import flask_cors
        print("✓ Flask-CORS is available")
    except ImportError:
        missing_packages.append("flask-cors")
    
    if missing_packages:
        print(f"\n✗ Missing dependencies: {', '.join(missing_packages)}")
        print("Please install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✓ All Python dependencies are available")
    return True

def initialize_database():
    """Initialize database with sample data if needed"""
    try:
        print("\nInitializing database...")
        db = DatabaseEngine()
        
        # Create sample tables if they don't exist
        if 'users' not in db.tables:
            print("Creating users table...")
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
            
            print("✓ Created users table with sample data")
        else:
            print("✓ Users table already exists")
        
        if 'products' not in db.tables:
            print("Creating products table...")
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
            
            print("✓ Created products table with sample data")
        else:
            print("✓ Products table already exists")
        
        # Create indexes if they don't exist
        try:
            db.create_index("users", "email", "idx_users_email")
            print("✓ Created index on users.email")
        except:
            print("✓ Index on users.email already exists")
        
        try:
            db.create_index("products", "category", "idx_products_category")
            print("✓ Created index on products.category")
        except:
            print("✓ Index on products.category already exists")
        
        print("✓ Database initialization completed")
        return True
        
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_server():
    """Start the Flask API server"""
    try:
        print("\n" + "="*60)
        print("🗄️  Starting Database Engine API Server")
        print("="*60)
        
        # Check if port is available
        if not check_port_available(5000):
            print("✗ Port 5000 is already in use!")
            print("Please stop any other services using port 5000 or change the port.")
            return False
        
        # Import and start the server
        from api_server import app
        
        print("✓ Server starting on http://localhost:5000")
        print("\nAPI endpoints:")
        print("  GET  /api/health - Health check")
        print("  GET  /api/tables - List all tables")
        print("  POST /api/sql - Execute SQL query")
        print("  GET  /api/database/stats - Database statistics")
        print("\n✓ Frontend should be available at http://localhost:3000")
        print("\nPress Ctrl+C to stop the server")
        print("="*60)
        
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped by user")
    except Exception as e:
        print(f"\n✗ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 Database Engine Startup")
    print("="*30)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 or higher is required")
        return False
    
    print(f"✓ Python {sys.version.split()[0]} detected")
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Create necessary directories
    os.makedirs("database", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("✓ Created necessary directories")
    
    # Initialize database
    if not initialize_database():
        return False
    
    # Start server
    return start_server()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✓ Startup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
