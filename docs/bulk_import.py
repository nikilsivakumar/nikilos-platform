"""
bulk_import.py
---------------
Reads docs/bulk_import.csv and, via the GitHub CLI (`gh`):
  1. Creates a GitHub Issue for every row (title, body, label).
  2. Adds that issue to your GitHub Project as an item.
  3. Sets the custom field values (Stage, Area, Type, Priority, Status,
     Decision) on that item to match the CSV row.

Every gh call is wrapped so you can see exactly what ran and what it
returned -- nothing here is hidden. If something fails partway through,
already-created issues stay created (this script is safe to re-run for
rows that failed; it doesn't delete or duplicate-check existing issues,
so re-running will create duplicates for rows that already succeeded --
see the SKIP_TITLES note at the bottom if you need to re-run partially).

BEFORE RUNNING:
  1. Install GitHub CLI:      winget install --id GitHub.cli
  2. Authenticate:            gh auth login   (choose GitHub.com, HTTPS, browser login)
  3. Create the project + all 6 custom fields + their options manually
     in the GitHub UI first (Stage, Area, Type, Priority, Status, Decision) --
     this script fills in VALUES for fields that must already exist.
     The option names in the CSV must match the option names you created
     in the UI EXACTLY (case-sensitive) or that field will be skipped
     for that row with a printed warning.
  4. Fill in the three config values directly below.

RUN (from the repo root, in cmd.exe, venv doesn't matter for this script):
    python docs/bulk_import.py
"""

import csv
import json
import subprocess
import sys

# ---- CONFIG: fill these in ----
REPO = "nikilsivakumar/nikilos-platform"      # owner/repo
PROJECT_OWNER = "nikilsivakumar"              # your GitHub username
PROJECT_NUMBER = 2                            # the number shown in your project's URL, e.g. .../projects/1
CSV_PATH = "docs/bulk_import.csv"
# --------------------------------


def run(args, capture=True):
    """
    Runs a gh command, prints it (so nothing is hidden), and returns stdout.
    Raises with the real gh error message on failure rather than swallowing it.
    """
    gh_path = r"C:\Program Files\GitHub CLI\gh.exe"
    print(f"  $ gh {' '.join(args)}")
    result = subprocess.run([gh_path] + args, capture_output=capture, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh command failed:\n{result.stderr}")
    return result.stdout.strip()


def ensure_label(label):
    """Creates a label if it doesn't already exist. Ignores the 'already exists' error."""
    if not label:
        return
    try:
        run(["label", "create", label, "--repo", REPO, "--color", "ededed", "--force"])
    except RuntimeError as e:
        print(f"    (label '{label}' likely already exists, continuing)")


def get_project_id_and_fields():
    """
    Fetches the project's internal node ID and a lookup of
    field_name -> {"id": field_id, "options": {option_name: option_id}}
    for every single-select field. We need these IDs because the API
    identifies fields/options by ID, not by the names you see in the UI.
    """
    project_json = run(["project", "view", str(PROJECT_NUMBER), "--owner", PROJECT_OWNER, "--format", "json"])
    project = json.loads(project_json)
    project_id = project["id"]

    fields_json = run(["project", "field-list", str(PROJECT_NUMBER), "--owner", PROJECT_OWNER, "--format", "json"])
    fields_data = json.loads(fields_json)["fields"]

    field_lookup = {}
    for f in fields_data:
        entry = {"id": f["id"], "options": {}}
        if "options" in f:
            for opt in f["options"]:
                entry["options"][opt["name"]] = opt["id"]
        field_lookup[f["name"]] = entry

    return project_id, field_lookup


def set_field(item_id, project_id, field_lookup, field_name, value):
    """
    Sets one single-select field on one project item. Skips quietly
    (with a warning) if the field or the option value doesn't exist --
    this usually means a typo between the CSV and what you created in
    the UI, worth checking rather than silently failing.
    """
    if not value:
        return
    field = field_lookup.get(field_name)
    if not field:
        print(f"    WARNING: field '{field_name}' not found in project -- skipping")
        return
    option_id = field["options"].get(value)
    if not option_id:
        print(f"    WARNING: option '{value}' not found under field '{field_name}' -- skipping")
        return
    run([
        "project", "item-edit",
        "--id", item_id,
        "--project-id", project_id,
        "--field-id", field["id"],
        "--single-select-option-id", option_id,
    ])


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} rows from {CSV_PATH}\n")

    print("Fetching project ID and field IDs...")
    project_id, field_lookup = get_project_id_and_fields()
    print(f"Project ID: {project_id}")
    print(f"Fields found: {list(field_lookup.keys())}\n")

    failures = []

    for i, row in enumerate(rows, start=1):
        title = row["Title"].strip()
        print(f"[{i}/{len(rows)}] {title}")

        try:
            ensure_label(row["Label"].strip())

            create_args = ["issue", "create", "--repo", REPO, "--title", title,
                            "--body", row["Body"].strip() or title]
            if row["Label"].strip():
                create_args += ["--label", row["Label"].strip()]
            issue_url = run(create_args)

            item_json = run(["project", "item-add", str(PROJECT_NUMBER), "--owner", PROJECT_OWNER,
                              "--url", issue_url, "--format", "json"])
            item_id = json.loads(item_json)["id"]

            for field_name in ["Stage", "Area", "Item Type", "Priority", "Status", "Decision"]:
                set_field(item_id, project_id, field_lookup, field_name, row.get(field_name, "").strip())

        except Exception as e:
            print(f"    FAILED: {e}")
            failures.append(title)

        print()

    print("Done.")
    if failures:
        print(f"\n{len(failures)} row(s) failed -- fix these manually or in the CSV then re-run just those:")
        for t in failures:
            print(f"  - {t}")


if __name__ == "__main__":
    main()
