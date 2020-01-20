import subprocess

# Create temporary database
subprocess.run(["./scripts/add_links_to_db", "-f", "tests/gettor.db"])
