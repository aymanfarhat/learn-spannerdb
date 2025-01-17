import click
import csv
from google.cloud import spanner
import logging
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
import numpy as np
from tqdm import tqdm
from schema_models import SchemaManifest, SchemaField, TableSchema

class SpannerIngestor:
    def __init__(self, project_id: str, instance_id: str, database_id: str):
        self.spanner_client = spanner.Client(project=project_id)
        self.instance = self.spanner_client.instance(instance_id)
        self.database = self.instance.database(database_id)
        self.logger = logging.getLogger(__name__)

    def _convert_value(self, value: Any, field: SchemaField) -> Any:
        """Convert CSV values to appropriate Spanner types based on schema field."""
        if pd.isna(value):
            if not field.nullable:
                raise ValueError(f"NULL value not allowed for non-nullable field {field.name}")
            return None

        if isinstance(value, str) and not value.strip():
            if not field.nullable:
                raise ValueError(f"Empty string not allowed for non-nullable field {field.name}")
            return None

        try:
            if field.type == 'INT64':
                return int(float(value)) if value is not None else None
            elif field.type == 'FLOAT64':
                return float(value) if value is not None else None
            elif field.type == 'BOOL':
                return bool(value) if value is not None else None
            elif field.type == 'TIMESTAMP':
                if isinstance(value, str):
                    # Try different date formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
                return value
            elif field.type.startswith('STRING'):
                str_value = str(value) if value is not None else None
                if str_value and field.length and len(str_value) > field.length:
                    raise ValueError(f"String value exceeds maximum length {field.length}")
                return str_value
            else:
                return value
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error converting value '{value}' to {field.type}: {str(e)}")
            if not field.nullable:
                raise
            return None

    def validate_foreign_keys(self, manifest: SchemaManifest, table_schema: TableSchema, 
                            data: pd.DataFrame) -> None:
        """Validate that foreign key relationships are satisfied."""
        if table_schema.parentTable:
            parent_schema = manifest.get_table_schema(table_schema.parentTable)
            if not parent_schema:
                raise ValueError(f"Parent table {table_schema.parentTable} schema not found")

            # Get parent key fields that should exist in child
            parent_keys = parent_schema.primaryKey

            # Validate all parent key fields exist in child
            missing_keys = [pk for pk in parent_keys if pk not in data.columns]
            if missing_keys:
                raise ValueError(f"Missing parent key fields: {missing_keys}")

    def ingest_csv(self, manifest: SchemaManifest, table_name: str, csv_file: str, 
                  batch_size: int = 500, validate_fk: bool = True) -> None:
        """Ingest CSV data into Spanner table using batch mutations."""
        # Get table schema
        table_schema = manifest.get_table_schema(table_name)
        if not table_schema:
            raise ValueError(f"Table {table_name} not found in schema manifest")

        # Create field lookup for easy access
        fields_by_name = {field.name: field for field in table_schema.schema}

        # Read CSV in chunks to handle large files
        chunk_iterator = pd.read_csv(
            csv_file, 
            chunksize=batch_size,
            dtype=str,  # Read all columns as strings initially
            na_values=['', 'NA', 'null', 'NULL', 'None', 'NaN'],
            keep_default_na=True
        )

        total_rows = sum(1 for _ in open(csv_file)) - 1  # Subtract header row
        progress_bar = tqdm(total=total_rows, desc="Ingesting data")

        for chunk in chunk_iterator:
            # Validate primary key fields are present
            missing_pks = [pk for pk in table_schema.primaryKey if pk not in chunk.columns]
            if missing_pks:
                raise ValueError(f"Missing primary key columns: {missing_pks}")

            # Validate foreign keys if requested
            if validate_fk:
                self.validate_foreign_keys(manifest, table_schema, chunk)

            # Validate required columns are present
            required_fields = [f.name for f in table_schema.schema if not f.nullable]
            missing_required = [field for field in required_fields if field not in chunk.columns]
            if missing_required:
                raise ValueError(f"Missing required columns: {missing_required}")

            # Prepare batch values
            columns = [field.name for field in table_schema.schema]
            values = []

            # Convert chunk data according to schema
            for _, row in chunk.iterrows():
                converted_row = []
                for col in columns:
                    field = fields_by_name[col]
                    converted_value = self._convert_value(row.get(col), field)
                    converted_row.append(converted_value)
                values.append(converted_row)

            # Execute batch mutation
            try:
                with self.database.batch() as batch:
                    batch.insert(
                        table=table_name,
                        columns=columns,
                        values=values
                    )
                progress_bar.update(len(chunk))
            except Exception as e:
                self.logger.error(f"Error inserting batch: {str(e)}")
                continue

        progress_bar.close()
        self.logger.info(f"Successfully ingested {total_rows} rows into {table_name}")

@click.command()
@click.option('--project-id', required=True, help='Google Cloud project ID')
@click.option('--instance-id', required=True, help='Spanner instance ID')
@click.option('--database-id', required=True, help='Spanner database ID')
@click.option('--schema-manifest', required=True, type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='Path to schema manifest JSON file')
@click.option('--table-name', required=True, help='Target table name')
@click.option('--csv-file', required=True, type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='Path to CSV file')
@click.option('--batch-size', default=500, help='Number of rows per batch')
@click.option('--skip-fk-validation', is_flag=True, help='Skip foreign key validation')
def main(project_id: str, instance_id: str, database_id: str, schema_manifest: str,
         table_name: str, csv_file: str, batch_size: int, skip_fk_validation: bool):
    """Ingest CSV data into a Cloud Spanner table using schema manifest."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Load schema manifest
        manifest = SchemaManifest(schema_manifest)

        # Initialize and run ingestion
        ingestor = SpannerIngestor(project_id, instance_id, database_id)
        ingestor.ingest_csv(manifest, table_name, csv_file, batch_size, not skip_fk_validation)
        click.echo(click.style('✓ Successfully completed data ingestion', fg='green'))
    except Exception as e:
        click.echo(click.style(f'Error: {str(e)}', fg='red'), err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()
