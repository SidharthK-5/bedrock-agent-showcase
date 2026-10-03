"""
Query Router Module
Analyzes user queries and determines which tables/schemas to query
"""

from typing import Any


class QueryRouter:
    """Routes user queries to appropriate database tables based on schema analysis"""

    def __init__(self, db_schema: dict[str, Any]):
        """
        Initialize query router with database schema

        Args:
            db_schema: Complete database schema structure
        """
        self.db_schema = db_schema
        self.schema_text = self._generate_schema_text()

    def _generate_schema_text(self) -> str:
        """
        Generate a text representation of the database schema

        Returns:
            Formatted string describing the database structure
        """
        schema_lines = []
        schema_lines.append("Database Schema Structure:")
        schema_lines.append("=" * 50)

        for schema_name, tables in self.db_schema.items():
            schema_lines.append(f"\nSchema: {schema_name}")
            schema_lines.append("-" * 40)

            for table_name, table_info in tables.items():
                schema_lines.append(f"  Table: {table_name}")
                schema_lines.append(f"    Type: {table_info['table_type']}")
                schema_lines.append("    Columns:")

                for col in table_info["columns"]:
                    nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                    schema_lines.append(
                        f"      - {col['column_name']} ({col['data_type']}) {nullable}"
                    )
                schema_lines.append("")

        return "\n".join(schema_lines)

    def get_schema_summary(self) -> str:
        """
        Get a summary of the database schema

        Returns:
            Schema summary string
        """
        return self.schema_text

    def find_relevant_tables(self, query: str) -> list[dict[str, str]]:
        """
        Find tables that might be relevant to the user's query
        This is a simple keyword-based approach

        Args:
            query: User's natural language query

        Returns:
            List of relevant table information
        """
        query_lower = query.lower()
        relevant_tables = []

        for schema_name, tables in self.db_schema.items():
            for table_name, table_info in tables.items():
                # Check if table name appears in query
                if table_name.lower() in query_lower:
                    relevant_tables.append(
                        {
                            "schema": schema_name,
                            "table": table_name,
                            "reason": "Table name matches query keywords",
                        }
                    )
                    continue

                # Check if any column names appear in query
                for col in table_info["columns"]:
                    if col["column_name"].lower() in query_lower:
                        relevant_tables.append(
                            {
                                "schema": schema_name,
                                "table": table_name,
                                "reason": f'Column "{col["column_name"]}" matches query keywords',
                            }
                        )
                        break

        return relevant_tables

    def build_sql_query(
        self, table_info: dict[str, str], filters: dict[str, Any] | None = None
    ) -> str:
        """
        Build a SQL query for a specific table

        Args:
            table_info: Dictionary with 'schema' and 'table' keys
            filters: Optional dictionary of column filters

        Returns:
            SQL query string
        """
        schema = table_info["schema"]
        table = table_info["table"]

        query = f'SELECT * FROM "{schema}"."{table}"'

        if filters:
            where_clauses = []
            for col, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"\"{col}\" = '{value}'")
                else:
                    where_clauses.append(f'"{col}" = {value}')

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

        query += " LIMIT 100;"

        return query

    def analyze_query_intent(self, user_query: str) -> dict[str, Any]:
        """
        Analyze user's query to determine intent and extract parameters

        Args:
            user_query: User's natural language query

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "query": user_query,
            "relevant_tables": self.find_relevant_tables(user_query),
            "schema_summary": self.get_schema_summary(),
        }

        return analysis
