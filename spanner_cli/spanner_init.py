import click
from google.cloud import spanner
import logging
from typing import List, Optional
from schema_models import SchemaManifest
from collections import defaultdict

class SpannerInitializer:
    def __init__(self, project_id: str, instance_id: str, database_id: str):
        """Initialize the SpannerInitializer with project, instance, and database details."""
        self.spanner_client = spanner.Client(project=project_id)
        self.instance = self.spanner_client.instance(instance_id)
        self.database = self.instance.database(database_id)
        self.logger = logging.getLogger(__name__)

    def _build_dependency_graph(self, manifest: SchemaManifest) -> List[List[str]]:
        """Build a dependency graph of tables based on parent-child relationships."""
        # Build adjacency list
        graph = defaultdict(list)
        roots = set(table.table for table in manifest.tables)

        for table in manifest.tables:
            if table.parentTable:
                graph[table.parentTable].append(table.table)
                if table.table in roots:
                    roots.remove(table.table)

        # Perform topological sort
        visited = set()
        temp_visited = set()
        order = []

        def visit(table: str):
            if table in temp_visited:
                raise ValueError(f"Circular dependency detected involving {table}")
            if table in visited:
                return

            temp_visited.add(table)
            for child in graph[table]:
                visit(child)
            temp_visited.remove(table)
            visited.add(table)
            order.append(table)

        # Start with root tables
        for root in roots:
            visit(root)

        # Group tables by level (for parallel creation where possible)
        levels = []
        current_level = []
        seen_parents = set()

        for table in order:
            table_schema = manifest.get_table_schema(table)
            if not table_schema or not table_schema.parentTable or table_schema.parentTable in seen_parents:
                current_level.append(table)
            else:
                if current_level:
                    levels.append(current_level)
                current_level = [table]
            seen_parents.add(table)

        if current_level:
            levels.append(current_level)

        return levels

    def create_tables(self, manifest: SchemaManifest) -> None:
        """Create tables defined in the schema manifest in the correct order."""
        # Get tables grouped by dependency level
        table_levels = self._build_dependency_graph(manifest)

        for level in table_levels:
            level_tables = [manifest.get_table_schema(table) for table in level]
            ddl_statements = [table.to_ddl() for table in level_tables if table]
            try:
                self.logger.info(f"Creating tables: {', '.join(level)}")
                for ddl in ddl_statements:
                    try:
                        operation = self.database.update_ddl([ddl])
                        operation.result()
                        self.logger.info(f"Successfully executed DDL:\n{ddl}")
                    except Exception as e:
                        # TODO: Better error handling, find the proper exception type to catch instead of string matching
                        if "Duplicate" in str(e):
                            self.logger.info(f"Table already exists, skipping")
                        else:
                            raise
            except Exception as e:
                self.logger.error(f"Error creating tables: {str(e)}")
                raise

@click.command()
@click.option('--project-id', required=True, help='Google Cloud project ID')
@click.option('--instance-id', required=True, help='Spanner instance ID')
@click.option('--database-id', required=True, help='Spanner database ID')
@click.option('--schema-manifest', required=True, type=click.Path(exists=True, file_okay=True, dir_okay=False),
              help='Path to schema manifest JSON file')
def main(project_id: str, instance_id: str, database_id: str, schema_manifest: str):
    """Initialize Spanner tables from a schema manifest."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Load schema manifest
        manifest = SchemaManifest(schema_manifest)

        # Initialize and run
        initializer = SpannerInitializer(project_id, instance_id, database_id)
        initializer.create_tables(manifest)

        click.echo(click.style('✓ Successfully initialized Spanner tables', fg='green'))
    except Exception as e:
        click.echo(click.style(f'Error: {str(e)}', fg='red'), err=True)
        raise click.Abort()

if __name__ == '__main__':
    main()
