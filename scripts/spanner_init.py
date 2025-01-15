import os
from google.cloud import spanner
from typing import List, Dict
import logging
import click

class SpannerInitializer:
    def __init__(self, project_id: str, instance_id: str, database_id: str):
        """
        Initialize the SpannerInitializer with project, instance, and database details.

        Args:
            project_id: Google Cloud project ID
            instance_id: Spanner instance ID
            database_id: Spanner database ID
        """
        self.spanner_client = spanner.Client(project=project_id)
        self.instance = self.spanner_client.instance(instance_id)
        self.database = self.instance.database(database_id)
        self.logger = logging.getLogger(__name__)

    def read_sql_file(self, file_path: str) -> str:
        """
        Read and return the contents of a SQL file.

        Args:
            file_path: Path to the SQL file

        Returns:
            str: Contents of the SQL file

        Raises:
            FileNotFoundError: If the SQL file doesn't exist
        """
        try:
            with open(file_path, 'r') as file:
                return file.read().strip()
        except FileNotFoundError:
            self.logger.error(f"SQL file not found: {file_path}")
            raise

    def parse_sql_files(self, schema_dir: str, index_dir: str) -> Dict[str, Dict[str, List[str]]]:
        """
        Parse SQL files from schema and index directories.

        Args:
            schema_dir: Directory containing table schema SQL files
            index_dir: Directory containing index SQL files

        Returns:
            Dict containing table schemas and their corresponding indexes
        """
        table_definitions = {}

        # Process schema files
        for schema_file in os.listdir(schema_dir):
            if schema_file.endswith('.sql'):
                table_name = os.path.splitext(schema_file)[0]
                schema_path = os.path.join(schema_dir, schema_file)
                table_definitions[table_name] = {
                    'schema': self.read_sql_file(schema_path),
                    'indexes': []
                }

        # Process index files
        for index_file in os.listdir(index_dir):
            if index_file.endswith('.sql'):
                index_path = os.path.join(index_dir, index_file)
                table_definitions[table_name]['indexes'].append(
                    self.read_sql_file(index_path)
                )

        return table_definitions

    def create_tables_and_indexes(self, schema_dir: str, index_dir: str) -> None:
        """
        Create tables and their corresponding indexes in Spanner.

        Args:
            schema_dir: Directory containing table schema SQL files
            index_dir: Directory containing index SQL files
        """
        table_definitions = self.parse_sql_files(schema_dir, index_dir)

        # Execute DDL statements for each table separately
        for table_name, definitions in table_definitions.items():
            try:
                # Try to create table first
                table_ddl = [definitions['schema']]
                try:
                    operation = self.database.update_ddl(table_ddl)
                    operation.result()  # Wait for the operation to complete
                    self.logger.info(f"Successfully created table {table_name}")
                except  Exception as e:
                    # TODO:: This is VERY bad, should find the correct exception to catch
                    if "Duplicate name in schema" in str(e):
                        self.logger.info(f"Table {table_name} already exists, skipping creation")
                    else:
                        self.logger.error(f"Error creating table {table_name}: {str(e)}")
                        raise

                # Try to create each index separately
                for index_ddl in definitions['indexes']:
                    try:
                        operation = self.database.update_ddl([index_ddl])
                        operation.result()
                        self.logger.info(f"Successfully created index on {table_name}")
                    except Exception as e:
                        if "Already exists" in str(e):
                            self.logger.info(f"Index on {table_name} already exists, skipping creation")
                        else:
                            self.logger.error(f"Error creating index on {table_name}: {str(e)}")
                            raise

            except Exception as e:
                self.logger.error(f"Error processing {table_name}: {str(e)}")
                raise

@click.command()
@click.option('--project-id', required=True, help='Google Cloud project ID')
@click.option('--instance-id', required=True, help='Spanner instance ID')
@click.option('--database-id', required=True, help='Spanner database ID')
@click.option('--schema-dir', required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Directory containing schema SQL files')
@click.option('--index-dir', required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Directory containing index SQL files')
def main(project_id: str, instance_id: str, database_id: str, schema_dir: str, index_dir: str):
    """Initialize Spanner tables and indexes from SQL definition files."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Initialize and run
        initializer = SpannerInitializer(
            project_id,
            instance_id,
            database_id
        )

        initializer.create_tables_and_indexes(schema_dir, index_dir)
        click.echo(click.style('✓ Successfully initialized Spanner tables and indexes', fg='green'))
    except Exception as e:
        click.echo(click.style(f'Error: {str(e)}', fg='red'), err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()
