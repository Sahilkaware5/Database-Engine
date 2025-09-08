import re
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

class TokenType(Enum):
    # Keywords
    SELECT = "SELECT"
    FROM = "FROM"
    WHERE = "WHERE"
    INSERT = "INSERT"
    INTO = "INTO"
    VALUES = "VALUES"
    CREATE = "CREATE"
    TABLE = "TABLE"
    DROP = "DROP"
    INDEX = "INDEX"
    ON = "ON"
    
    # Data types
    INT = "INT"
    VARCHAR = "VARCHAR"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    
    # Literals
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    
    # Operators
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    LIKE = "LIKE"
    
    # Punctuation
    SEMICOLON = ";"
    COMMA = ","
    LPAREN = "("
    RPAREN = ")"
    ASTERISK = "*"
    
    # Special
    EOF = "EOF"
    WHITESPACE = "WHITESPACE"

@dataclass
class Token:
    type: TokenType
    value: str
    position: int

class SQLTokenizer:
    def __init__(self):
        self.keywords = {
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES',
            'CREATE', 'TABLE', 'DROP', 'INDEX', 'ON',
            'INT', 'VARCHAR', 'FLOAT', 'BOOLEAN', 'DATE',
            'LIKE', 'AND', 'OR', 'NOT', 'NULL'
        }
        
        self.operators = {
            '=': TokenType.EQUALS,
            '!=': TokenType.NOT_EQUALS,
            '>': TokenType.GREATER,
            '<': TokenType.LESS,
            '>=': TokenType.GREATER_EQUAL,
            '<=': TokenType.LESS_EQUAL,
        }
        
        self.punctuation = {
            ';': TokenType.SEMICOLON,
            ',': TokenType.COMMA,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '*': TokenType.ASTERISK,
        }
    
    def tokenize(self, sql: str) -> List[Token]:
        """Convert SQL string into tokens"""
        tokens = []
        position = 0
        sql = sql.strip()
        
        while position < len(sql):
            # Skip whitespace
            if sql[position].isspace():
                position += 1
                continue
            
            # String literals
            if sql[position] in ('"', "'"):
                quote_char = sql[position]
                start_pos = position
                position += 1
                
                while position < len(sql) and sql[position] != quote_char:
                    position += 1
                
                if position < len(sql):
                    position += 1  # Skip closing quote
                
                value = sql[start_pos + 1:position - 1]
                tokens.append(Token(TokenType.STRING, value, start_pos))
                continue
            
            # Numbers
            if sql[position].isdigit():
                start_pos = position
                while position < len(sql) and (sql[position].isdigit() or sql[position] == '.'):
                    position += 1
                
                value = sql[start_pos:position]
                tokens.append(Token(TokenType.NUMBER, value, start_pos))
                continue
            
            # Multi-character operators
            if position < len(sql) - 1:
                two_char = sql[position:position + 2]
                if two_char in self.operators:
                    tokens.append(Token(self.operators[two_char], two_char, position))
                    position += 2
                    continue
            
            # Single-character operators and punctuation
            if sql[position] in self.operators:
                char = sql[position]
                tokens.append(Token(self.operators[char], char, position))
                position += 1
                continue
            
            if sql[position] in self.punctuation:
                char = sql[position]
                tokens.append(Token(self.punctuation[char], char, position))
                position += 1
                continue
            
            # Identifiers and keywords
            if sql[position].isalpha() or sql[position] == '_':
                start_pos = position
                while position < len(sql) and (sql[position].isalnum() or sql[position] == '_'):
                    position += 1
                
                value = sql[start_pos:position]
                
                # Check if it's a keyword
                if value.upper() in self.keywords:
                    token_type = TokenType[value.upper()]
                else:
                    token_type = TokenType.IDENTIFIER
                
                tokens.append(Token(token_type, value, start_pos))
                continue
            
            # Unknown character
            raise SyntaxError(f"Unexpected character '{sql[position]}' at position {position}")
        
        tokens.append(Token(TokenType.EOF, "", len(sql)))
        return tokens

@dataclass
class SelectStatement:
    columns: List[str]
    table_name: str
    where_clause: Optional[Dict] = None

@dataclass
class InsertStatement:
    table_name: str
    columns: List[str]
    values: List[Any]

@dataclass
class CreateTableStatement:
    table_name: str
    columns: List[Dict]

@dataclass
class CreateIndexStatement:
    index_name: str
    table_name: str
    column_name: str

class SQLParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
    
    def current_token(self) -> Token:
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return Token(TokenType.EOF, "", -1)
    
    def advance(self):
        if self.position < len(self.tokens) - 1:
            self.position += 1
    
    def consume(self, expected_type: TokenType):
        token = self.current_token()
        if token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token.type}")
        self.advance()
        return token
    
    def parse(self):
        """Parse tokens into AST"""
        token = self.current_token()
        
        if token.type == TokenType.SELECT:
            return self.parse_select()
        elif token.type == TokenType.INSERT:
            return self.parse_insert()
        elif token.type == TokenType.CREATE:
            return self.parse_create()
        elif token.type == TokenType.DROP:
            return self.parse_drop()
        else:
            raise SyntaxError(f"Unsupported SQL statement starting with {token.type}")
    
    def parse_select(self) -> SelectStatement:
        """Parse SELECT statement"""
        self.consume(TokenType.SELECT)
        
        # Parse columns
        columns = []
        if self.current_token().type == TokenType.ASTERISK:
            columns = ['*']
            self.advance()
        else:
            columns.append(self.current_token().value)
            self.advance()
            
            while self.current_token().type == TokenType.COMMA:
                self.advance()  # Skip comma
                columns.append(self.current_token().value)
                self.advance()
        
        # Parse FROM clause
        self.consume(TokenType.FROM)
        table_name = self.current_token().value
        self.advance()
        
        # Parse optional WHERE clause
        where_clause = None
        if self.current_token().type == TokenType.WHERE:
            where_clause = self.parse_where_clause()
        
        return SelectStatement(columns, table_name, where_clause)
    
    def parse_where_clause(self) -> Dict:
        """Parse WHERE clause"""
        self.consume(TokenType.WHERE)
        
        column = self.current_token().value
        self.advance()
        
        operator_token = self.current_token()
        operator = operator_token.value
        self.advance()
        
        # Parse value
        value_token = self.current_token()
        if value_token.type == TokenType.STRING:
            value = value_token.value
        elif value_token.type == TokenType.NUMBER:
            value = float(value_token.value) if '.' in value_token.value else int(value_token.value)
        else:
            value = value_token.value
        
        self.advance()
        
        return {
            'column': column,
            'operator': operator,
            'value': value
        }
    
    def parse_insert(self) -> InsertStatement:
        """Parse INSERT statement"""
        self.consume(TokenType.INSERT)
        self.consume(TokenType.INTO)
        
        table_name = self.current_token().value
        self.advance()
        
        # Parse optional column list
        columns = []
        if self.current_token().type == TokenType.LPAREN:
            self.advance()  # Skip '('
            
            columns.append(self.current_token().value)
            self.advance()
            
            while self.current_token().type == TokenType.COMMA:
                self.advance()  # Skip comma
                columns.append(self.current_token().value)
                self.advance()
            
            self.consume(TokenType.RPAREN)
        
        # Parse VALUES clause
        self.consume(TokenType.VALUES)
        self.consume(TokenType.LPAREN)
        
        values = []
        value_token = self.current_token()
        if value_token.type == TokenType.STRING:
            values.append(value_token.value)
        elif value_token.type == TokenType.NUMBER:
            values.append(float(value_token.value) if '.' in value_token.value else int(value_token.value))
        else:
            values.append(value_token.value)
        self.advance()
        
        while self.current_token().type == TokenType.COMMA:
            self.advance()  # Skip comma
            value_token = self.current_token()
            if value_token.type == TokenType.STRING:
                values.append(value_token.value)
            elif value_token.type == TokenType.NUMBER:
                values.append(float(value_token.value) if '.' in value_token.value else int(value_token.value))
            else:
                values.append(value_token.value)
            self.advance()
        
        self.consume(TokenType.RPAREN)
        
        return InsertStatement(table_name, columns, values)
    
    def parse_create(self):
        """Parse CREATE statement"""
        self.consume(TokenType.CREATE)
        
        if self.current_token().type == TokenType.TABLE:
            return self.parse_create_table()
        elif self.current_token().type == TokenType.INDEX:
            return self.parse_create_index()
        else:
            raise SyntaxError("Expected TABLE or INDEX after CREATE")
    
    def parse_create_table(self) -> CreateTableStatement:
        """Parse CREATE TABLE statement"""
        self.consume(TokenType.TABLE)
        
        table_name = self.current_token().value
        self.advance()
        
        self.consume(TokenType.LPAREN)
        
        # Parse column definitions
        columns = []
        while self.current_token().type != TokenType.RPAREN:
            col_name = self.current_token().value
            self.advance()
            
            col_type = self.current_token().value
            self.advance()
            
            # Handle type parameters like VARCHAR(50)
            size = None
            if self.current_token().type == TokenType.LPAREN:
                self.advance()  # Skip '('
                size = int(self.current_token().value)
                self.advance()  # Skip size
                self.consume(TokenType.RPAREN)
            
            columns.append({
                'name': col_name,
                'type': col_type,
                'size': size
            })
            
            if self.current_token().type == TokenType.COMMA:
                self.advance()
        
        self.consume(TokenType.RPAREN)
        
        return CreateTableStatement(table_name, columns)
    
    def parse_create_index(self) -> CreateIndexStatement:
        """Parse CREATE INDEX statement"""
        self.consume(TokenType.INDEX)
        
        index_name = self.current_token().value
        self.advance()
        
        self.consume(TokenType.ON)
        
        table_name = self.current_token().value
        self.advance()
        
        self.consume(TokenType.LPAREN)
        column_name = self.current_token().value
        self.advance()
        self.consume(TokenType.RPAREN)
        
        return CreateIndexStatement(index_name, table_name, column_name)

class SQLExecutor:
    """Execute parsed SQL statements"""
    
    def __init__(self, database_engine):
        self.db = database_engine
    
    def execute(self, statement):
        """Execute a parsed SQL statement"""
        if isinstance(statement, SelectStatement):
            return self.execute_select(statement)
        elif isinstance(statement, InsertStatement):
            return self.execute_insert(statement)
        elif isinstance(statement, CreateTableStatement):
            return self.execute_create_table(statement)
        elif isinstance(statement, CreateIndexStatement):
            return self.execute_create_index(statement)
        else:
            raise ValueError(f"Unsupported statement type: {type(statement)}")
    
    def execute_select(self, statement: SelectStatement):
        """Execute SELECT statement"""
        columns = None if statement.columns == ['*'] else statement.columns
        return self.db.select_from(statement.table_name, statement.where_clause, columns)
    
    def execute_insert(self, statement: InsertStatement):
        """Execute INSERT statement"""
        if statement.columns:
            record = dict(zip(statement.columns, statement.values))
        else:
            # Assume values are in column order
            table = self.db.tables[statement.table_name]
            record = dict(zip(table.column_order, statement.values))
        
        self.db.insert_into(statement.table_name, record)
        return f"1 row inserted into {statement.table_name}"
    
    def execute_create_table(self, statement: CreateTableStatement):
        """Execute CREATE TABLE statement"""
        from storage_engine import Column, DataType
        
        columns = []
        for col_def in statement.columns:
            data_type = DataType(col_def['type'].upper())
            columns.append(Column(
                name=col_def['name'],
                data_type=data_type,
                size=col_def.get('size')
            ))
        
        self.db.create_table(statement.table_name, columns)
        return f"Table {statement.table_name} created"
    
    def execute_create_index(self, statement: CreateIndexStatement):
        """Execute CREATE INDEX statement"""
        self.db.create_index(statement.table_name, statement.column_name, statement.index_name)
        return f"Index {statement.index_name} created"

def execute_sql(sql: str, database_engine):
    """Execute SQL string"""
    try:
        tokenizer = SQLTokenizer()
        tokens = tokenizer.tokenize(sql)
        
        parser = SQLParser(tokens)
        statement = parser.parse()
        
        executor = SQLExecutor(database_engine)
        result = executor.execute(statement)
        
        return {'success': True, 'result': result}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Example usage
if __name__ == "__main__":
    from storage_engine import DatabaseEngine
    
    # Create database
    db = DatabaseEngine()
    
    # Test SQL execution
    sql_commands = [
        "CREATE TABLE users (id INT, name VARCHAR(50), email VARCHAR(100))",
        "INSERT INTO users (id, name, email) VALUES (1, 'John Doe', 'john@example.com')",
        "INSERT INTO users VALUES (2, 'Jane Smith', 'jane@example.com')",
        "SELECT * FROM users",
        "SELECT name, email FROM users WHERE id = 1",
        "CREATE INDEX idx_email ON users (email)"
    ]
    
    for sql in sql_commands:
        print(f"Executing: {sql}")
        result = execute_sql(sql, db)
        print(f"Result: {result}")
        print("-" * 50)
