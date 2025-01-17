from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
import json

class SchemaField(BaseModel):
    """Represents a single field in a Spanner table schema."""
    name: str
    type: str
    nullable: bool = True
    length: Optional[int] = None

    def to_ddl(self) -> str:
        """Convert the field to Spanner DDL syntax."""
        ddl_type = self.type
        if self.type == "STRING" and self.length:
            ddl_type = f"STRING({self.length})"
        elif self.type == "STRING" and not self.length:
            ddl_type = "STRING(MAX)"

        nullability = "" if self.nullable else " NOT NULL"
        return f"{self.name} {ddl_type}{nullability}"

class TableSchema(BaseModel):
    """Represents a complete table schema with primary key and relationships."""
    table: str
    schema: List[SchemaField]
    primaryKey: List[str]
    foreignKeys: Optional[List[Dict[str, str]]] = None
    parentTable: Optional[str] = None
    onParentDelete: Optional[Literal["CASCADE", "NO ACTION"]] = None

    def to_ddl(self) -> str:
        """Generate CREATE TABLE DDL for this schema."""
        # Generate field definitions
        fields_ddl = ",".join(field.to_ddl() for field in self.schema)

        # Add primary key constraint
        pk_clause = f"PRIMARY KEY({','.join(self.primaryKey)})"

        # Add interleave clause if parent table is specified
        interleave_clause = ""
        if self.parentTable:
            cascade = "CASCADE" if self.onParentDelete == "CASCADE" else "NO ACTION"
            interleave_clause = f") INTERLEAVE IN PARENT {self.parentTable} ON DELETE {cascade}"
            return f"""CREATE TABLE {self.table} (
    {fields_ddl}{pk_clause}{interleave_clause}"""

        fk_clause = ""

        if self.foreignKeys:
            for fk in self.foreignKeys:
                fk_clause += f"CONSTRAINT {fk['name']} FOREIGN KEY ({fk['field']}) REFERENCES {fk['refTable']}({fk['refField']}) ON DELETE {fk['onDelete']}," 

        return f"""CREATE TABLE {self.table} ({fields_ddl},{fk_clause}) {pk_clause}"""
    def validate_primary_key(self) -> None:
        """Validate that primary key fields exist and are not nullable."""
        schema_fields = {field.name: field for field in self.schema}
        for pk_field in self.primaryKey:
            if pk_field not in schema_fields:
                raise ValueError(f"Primary key field {pk_field} not found in schema")
            if schema_fields[pk_field].nullable:
                raise ValueError(f"Primary key field {pk_field} must not be nullable")

class SchemaManifest:
    """Handles loading and managing schema definitions."""
    def __init__(self, manifest_path: str):
        self.tables: List[TableSchema] = []
        self.load_manifest(manifest_path)

    def load_manifest(self, manifest_path: str) -> None:
        """Load schema definitions from a JSON manifest file."""
        with open(manifest_path, 'r') as f:
            schemas = json.load(f)
            # First, create all table schemas
            self.tables = [TableSchema(**schema) for schema in schemas['tables']]

            # Then validate relationships
            self._validate_relationships()

            # Finally validate primary keys
            for table in self.tables:
                table.validate_primary_key()

    def _validate_relationships(self) -> None:
        """Validate parent-child relationships between tables."""
        table_names = {table.table for table in self.tables}
        for table in self.tables:
            if table.parentTable and table.parentTable not in table_names:
                raise ValueError(
                    f"Parent table {table.parentTable} for {table.table} not found in schema"
                )

    def get_table_schema(self, table_name: str) -> Optional[TableSchema]:
        """Get schema for a specific table."""
        for table in self.tables:
            if table.table == table_name:
                return table
        return None

    def get_field_types(self, table_name: str) -> Dict[str, str]:
        """Get a mapping of field names to their Spanner types for a table."""
        table = self.get_table_schema(table_name)
        if table:
            return {field.name: field.type for field in table.schema}
        return {}
