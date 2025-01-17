uv run spanner_load.py \
  --project-id="workflows-demo-369108" \
  --instance-id="tfgen-spanid-20250112075614261" \
  --database-id="coredb" \
  --schema-manifest=/Users/aymanf/projects/learn-spannerdb/examples/schema_manifest.json \
  --table-name="Investment" \
  --csv-file="/Users/aymanf/projects/learn-spannerdb/examples/raw_data/investments.csv" \
  --batch-size=100

#uv run spanner_load.py \
#  --project-id="workflows-demo-369108" \
#  --instance-id="tfgen-spanid-20250112075614261" \
#  --database-id="coredb" \
#  --schema-manifest=/Users/aymanf/projects/learn-spannerdb/examples/schema_manifest.json \
#  --table-name="Object" \
#  --csv-file="/Users/aymanf/projects/learn-spannerdb/examples/raw_data/objects.csv" \
#  --batch-size=1500

#uv run spanner_load.py \
#  --project-id="workflows-demo-369108" \
#  --instance-id="tfgen-spanid-20250112075614261" \
#  --database-id="coredb" \
#  --schema-manifest=/Users/aymanf/projects/learn-spannerdb/examples/schema_manifest.json \
#  --table-name="FundingRound" \
#  --csv-file="/Users/aymanf/projects/learn-spannerdb/examples/raw_data/funding_rounds.csv" \
#  --batch-size=2000
