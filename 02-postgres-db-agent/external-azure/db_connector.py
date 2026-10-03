"""
Database connector module for PostgreSQL
Handles connection, schema introspection, and query execution
"""

from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class DatabaseConnector:
    """Handles PostgreSQL database connections and operations"""

    def __init__(self, connection_uri: str):
        """
        Initialize database connector

        Args:
            connection_uri: PostgreSQL connection URI
        """
        self.connection_uri = connection_uri
        self.engine: Engine = None
        self.connection = None

    def connect(self):
        """Establish database connection"""
        try:
            self.engine = create_engine(
                self.connection_uri, pool_pre_ping=True, pool_recycle=3600, echo=False
            )
            self.connection = self.engine.connect()
            return True
        except Exception as e:
            print(f"Database connection error: {e!s}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def get_all_schemas(self) -> list[dict[str, Any]]:
        """
        Get all schema names in the database

        Returns:
            List of schema name dictionaries
        """
        query = text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)
        return self._execute_query(query)

    def get_tables_in_schema(self, schema_name: str = "public") -> list[dict[str, Any]]:
        """
        Get all tables in a specific schema

        Args:
            schema_name: Schema name (default: 'public')

        Returns:
            List of table information dictionaries
        """
        query = text("""
            SELECT 
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables 
            WHERE table_schema = :schema_name
            ORDER BY table_name;
        """)
        return self._execute_query(query, {"schema_name": schema_name})

    def get_table_schema(
        self, table_name: str, schema_name: str = "public"
    ) -> list[dict[str, Any]]:
        """
        Get detailed schema information for a specific table

        Args:
            table_name: Name of the table
            schema_name: Schema name (default: 'public')

        Returns:
            List of column information dictionaries
        """
        query = text("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = :schema_name AND table_name = :table_name
            ORDER BY ordinal_position;
        """)
        return self._execute_query(
            query, {"schema_name": schema_name, "table_name": table_name}
        )

    def get_complete_database_schema(self) -> dict[str, Any]:
        """
        Get complete database schema structure

        Returns:
            Dictionary containing all schemas, tables, and columns
        """
        schemas = self.get_all_schemas()
        database_structure = {}

        for schema_row in schemas:
            schema_name = schema_row.get("schema_name", "public")
            database_structure[schema_name] = {}

            tables = self.get_tables_in_schema(schema_name)

            for table_row in tables:
                table_name = table_row["table_name"]
                columns = self.get_table_schema(table_name, schema_name)

                database_structure[schema_name][table_name] = {
                    "table_type": table_row["table_type"],
                    "columns": columns,
                }

        return database_structure

    def execute_custom_query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute a custom SQL query

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of result dictionaries
        """
        # Wrap raw SQL strings in text()
        if isinstance(query, str):
            query = text(query)
        return self._execute_query(query, params)

    def _execute_query(
        self, query, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Internal method to execute queries and return results

        Args:
            query: SQLAlchemy text object or SQL query string
            params: Query parameters dictionary (optional)

        Returns:
            List of result dictionaries
        """
        try:
            # Execute the query
            if params:
                result = self.connection.execute(query, params)
            else:
                result = self.connection.execute(query)

            # Check if query returns results
            if result.returns_rows:
                # Fetch all results and convert to list of dictionaries
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
            else:
                # For INSERT, UPDATE, DELETE operations
                self.connection.commit()
                return []

        except Exception as e:
            print(f"Query execution error: {e!s}")
            if self.connection:
                self.connection.rollback()
            raise

    def get_table_sample_data(
        self, table_name: str, schema_name: str = "public", limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get sample data from a table

        Args:
            table_name: Name of the table
            schema_name: Schema name (default: 'public')
            limit: Number of rows to return (default: 5)

        Returns:
            List of sample row dictionaries
        """
        query = text(f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT :limit')
        return self._execute_query(query, {"limit": limit})
