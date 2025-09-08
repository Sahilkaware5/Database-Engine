from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import traceback
from storage_engine import DatabaseEngine, Column, DataType
from sql_parser import execute_sql

app = Flask(__name__)

# Configure CORS to allow all origins in development
CORS(app, origins=["*"], allow_headers=["Content-Type"], methods=["GET", "POST", "DELETE", "OPTIONS"])

# Global database instance
db = DatabaseEngine()

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    print(f"Unhandled exception: {e}")
    print(traceback.format_exc())
    return jsonify({
        'success': False, 
        'error': f'Internal server error: {str(e)}'
    }), 500

@app.before_request
def log_request():
    """Log incoming requests"""
    print(f"{request.method} {request.path} - {request.remote_addr}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        tables = db.list_tables()
        return jsonify({
            'status': 'healthy', 
            'message': 'Database engine is running',
            'tables_count': len(tables)
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}'
        }), 503

@app.route('/api/tables', methods=['GET'])
def list_tables():
    """List all tables in the database"""
    try:
        tables = db.list_tables()
        return jsonify({'success': True, 'tables': tables})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tables/<table_name>', methods=['GET'])
def get_table_info(table_name):
    """Get information about a specific table"""
    try:
        table_info = db.get_table_info(table_name)
        return jsonify({'success': True, 'table': table_info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@app.route('/api/tables/<table_name>/data', methods=['GET'])
def get_table_data(table_name):
    """Get data from a table with optional pagination"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get all data (we'll implement proper pagination later)
        data = db.select_from(table_name)
        
        # Simple pagination
        paginated_data = data[offset:offset + limit]
        
        return jsonify({
            'success': True,
            'data': paginated_data,
            'total': len(data),
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sql', methods=['POST'])
def execute_sql_endpoint():
    """Execute SQL query"""
    try:
        data = request.get_json()
        sql_query = data.get('sql', '').strip()
        
        if not sql_query:
            return jsonify({'success': False, 'error': 'SQL query is required'}), 400
        
        result = execute_sql(sql_query, db)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tables', methods=['POST'])
def create_table():
    """Create a new table"""
    try:
        data = request.get_json()
        table_name = data.get('name')
        columns_data = data.get('columns', [])
        
        if not table_name or not columns_data:
            return jsonify({'success': False, 'error': 'Table name and columns are required'}), 400
        
        # Convert column data to Column objects
        columns = []
        for col_data in columns_data:
            data_type = DataType(col_data['type'].upper())
            columns.append(Column(
                name=col_data['name'],
                data_type=data_type,
                size=col_data.get('size'),
                primary_key=col_data.get('primary_key', False),
                nullable=col_data.get('nullable', True),
                default_value=col_data.get('default_value')
            ))
        
        db.create_table(table_name, columns)
        
        return jsonify({'success': True, 'message': f'Table {table_name} created successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tables/<table_name>', methods=['DELETE'])
def drop_table(table_name):
    """Drop a table"""
    try:
        db.drop_table(table_name)
        return jsonify({'success': True, 'message': f'Table {table_name} dropped successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tables/<table_name>/records', methods=['POST'])
def insert_record(table_name):
    """Insert a record into a table"""
    try:
        data = request.get_json()
        record = data.get('record', {})
        
        if not record:
            return jsonify({'success': False, 'error': 'Record data is required'}), 400
        
        db.insert_into(table_name, record)
        
        return jsonify({'success': True, 'message': 'Record inserted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/database/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        tables = db.list_tables()
        stats = {
            'total_tables': len(tables),
            'tables': {}
        }
        
        total_records = 0
        for table_name in tables:
            table_info = db.get_table_info(table_name)
            stats['tables'][table_name] = {
                'records': table_info['total_records'],
                'pages': table_info['total_pages'],
                'columns': len(table_info['columns']),
                'indexes': len(table_info['indexes'])
            }
            total_records += table_info['total_records']
        
        stats['total_records'] = total_records
        
        return jsonify({'success': True, 'stats': stats})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tables/<table_name>/indexes', methods=['POST'])
def create_index(table_name):
    """Create an index on a table column"""
    try:
        data = request.get_json()
        column_name = data.get('column')
        index_name = data.get('name')
        
        if not column_name or not index_name:
            return jsonify({'success': False, 'error': 'Column name and index name are required'}), 400
        
        db.create_index(table_name, column_name, index_name)
        
        return jsonify({'success': True, 'message': f'Index {index_name} created successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize with some sample data
    try:
        # Create sample tables if they don't exist
        if 'users' not in db.tables:
            user_columns = [
                Column("id", DataType.INT, primary_key=True),
                Column("name", DataType.VARCHAR, size=50, nullable=False),
                Column("email", DataType.VARCHAR, size=100),
                Column("age", DataType.INT, default_value=0)
            ]
            db.create_table("users", user_columns)
            
            # Insert sample data
            db.insert_into("users", {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30})
            db.insert_into("users", {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25})
            db.insert_into("users", {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35})
        
        if 'products' not in db.tables:
            product_columns = [
                Column("id", DataType.INT, primary_key=True),
                Column("name", DataType.VARCHAR, size=100, nullable=False),
                Column("price", DataType.FLOAT),
                Column("category", DataType.VARCHAR, size=50)
            ]
            db.create_table("products", product_columns)
            
            # Insert sample data
            db.insert_into("products", {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"})
            db.insert_into("products", {"id": 2, "name": "Book", "price": 19.99, "category": "Education"})
            db.insert_into("products", {"id": 3, "name": "Coffee Mug", "price": 12.50, "category": "Kitchen"})
    
    except Exception as e:
        print(f"Error initializing sample data: {e}")
    
    print("Starting Database Engine API Server...")
    print("API will be available at http://localhost:5000")
    print("Available endpoints:")
    print("  GET  /api/health - Health check")
    print("  GET  /api/tables - List all tables")
    print("  POST /api/sql - Execute SQL query")
    print("  GET  /api/database/stats - Database statistics")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
