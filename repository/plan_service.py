import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List
from .plan_models import PlanStatus, Plan, PlanData, PlanLoadResult, LoadError


class PlanService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        # Ensure directory structure exists
        self.check_dirs()

    def check_dirs(self) -> bool:
        """Check if all required plan directories exist, create them if missing

        Returns:
            bool: True if all directories exist or were created successfully,
            False on error
        """
        project_dir = Path(__file__).parent.parent
        plans_dir = project_dir / "_docs" / "plans"

        # Required directories
        required_dirs = [
            plans_dir,
            plans_dir / "drafts",
            plans_dir / "approved",
            plans_dir / "completed"
        ]

        missing_dirs = []
        created_dirs = []

        for dir_path in required_dirs:
            if not dir_path.exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            print("📁 Creating missing plan directories:")
            for missing_dir in missing_dirs:
                try:
                    missing_dir.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(missing_dir)
                    print(f"   ✅ Created: {
                          missing_dir.relative_to(project_dir)}")
                except Exception as e:
                    print(f"   ❌ Failed to create {
                          missing_dir.relative_to(project_dir)}: {e}")
                    return False

            if created_dirs:
                print(f"📁 Successfully created {
                      len(created_dirs)} directories")
        else:
            print("✅ All required plan directories exist")

        return True

    def files_to_plans(self, plans_data: dict) -> List[Plan]:
        """Convert raw plans data to List[Plan] objects

        Args:
            plans_data: Dictionary from load_files containing file data

        Returns:
            List[Plan]: List of Plan objects created from the files
        """
        plans = []
        current_time = datetime.now()

        for status, data in plans_data.items():
            # Skip directories with errors
            if "error" in data:
                continue

            files = data.get("files", [])

            for file_info in files:
                # Skip files with errors
                if "error" in file_info:
                    continue

                try:
                    # Generate unique ID from filename (remove .md extension)
                    file_stem = Path(file_info["name"]).stem
                    plan_id = f"{status.value}_{file_stem}"

                    # Calculate content hash
                    content_hash = hashlib.sha256(
                        file_info["content"].encode('utf-8')
                    ).hexdigest()

                    # Create PlanData object
                    plan_data = PlanData(
                        status=status,
                        markdown_content=file_info["content"],
                        description=f"Plan loaded from {file_info['path']}",
                        tags=[status.value],  # Add status as a tag
                        metadata={
                            "file_size": file_info["file_size"],
                            "original_path": str(file_info["path"])
                        }
                    )

                    # Create Plan object
                    plan = Plan(
                        id=plan_id,
                        name=file_stem.replace(
                            "_", " ").replace("-", " ").title(),
                        data=plan_data,
                        version=1,
                        content_hash=content_hash,
                        created_at=current_time,
                        updated_at=current_time
                    )

                    plans.append(plan)

                except Exception as e:
                    print(f"❌ Error converting {file_info.get(
                        'name', 'unknown')} to Plan: {e}")
                    continue

        return plans

    def load_database(self, plans: List[Plan]) -> PlanLoadResult:
        """Load plans into the database

        Args:
            plans: List of Plan objects to load into database

        Returns:
            PlanLoadResult: Summary of the loading operation
        """
        loaded_plans = []
        skipped_plans = []
        errors = []

        cursor = self.conn.cursor()

        for plan in plans:
            try:
                # Check if plan already exists (by ID and content hash)
                cursor.execute("""
                    SELECT id, content_hash FROM plans 
                    WHERE id = ? AND content_hash = ?
                """, (plan.id, plan.content_hash))

                existing = cursor.fetchone()

                if existing:
                    # Plan already exists with same content, skip
                    skipped_plans.append(plan.id)
                    continue

                # Check if plan exists with different content (update scenario)
                cursor.execute("SELECT id FROM plans WHERE id = ?", (plan.id,))
                needs_update = cursor.fetchone() is not None

                # Serialize PlanData to JSON for JSONB storage
                plan_data_json = plan.data.model_dump_json()

                if needs_update:
                    # Update existing plan
                    cursor.execute("""
                        UPDATE plans 
                        SET name = ?, data = jsonb(?), version = version + 1, 
                            content_hash = ?, updated_at = ?
                        WHERE id = ?
                    """, (
                        plan.name,
                        plan_data_json,
                        plan.content_hash,
                        plan.updated_at,
                        plan.id
                    ))
                else:
                    # Insert new plan
                    cursor.execute("""
                        INSERT INTO plans (id, name, data, version, content_hash, created_at, updated_at)
                        VALUES (?, ?, jsonb(?), ?, ?, ?, ?)
                    """, (
                        plan.id,
                        plan.name,
                        plan_data_json,
                        plan.version,
                        plan.content_hash,
                        plan.created_at,
                        plan.updated_at
                    ))

                loaded_plans.append(plan.id)

            except Exception as e:
                error = LoadError(
                    filename=plan.id,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                errors.append(error)

        # Commit all changes
        try:
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            # Add a general commit error
            error = LoadError(
                filename="database_commit",
                error_message=f"Failed to commit changes: {str(e)}",
                error_type=type(e).__name__
            )
            errors.append(error)

        return PlanLoadResult(
            loaded_count=len(loaded_plans),
            skipped_count=len(skipped_plans),
            error_count=len(errors),
            loaded_plans=loaded_plans,
            skipped_plans=skipped_plans,
            errors=errors if errors else None
        )

    def load_files(self):
        """Read and display all plans from _docs/plans directory structure"""

        project_dir = Path(__file__).parent.parent
        plans_dir = project_dir / "_docs" / "plans"

        # Map directory names to PlanStatus enum values
        status_mapping = {
            "drafts": PlanStatus.DRAFT,
            "approved": PlanStatus.APPROVED,
            "completed": PlanStatus.COMPLETED
        }

        # Collect plan data
        plans_data = {}
        total_files = 0

        # Iterate through each status directory
        for dir_name, status in status_mapping.items():
            status_dir = plans_dir / dir_name

            if not status_dir.exists():
                plans_data[status] = {
                    "error": f"Directory not found: {status_dir}", "files": []}
                continue

            # Find all .md files in this status directory
            md_files = list(status_dir.glob("*.md"))

            plans_data[status] = {"files": []}

            for md_file in sorted(md_files):
                try:
                    # Read file content to get size info
                    content = md_file.read_text(encoding='utf-8')
                    file_size = len(content)

                    plan_info = {
                        "name": md_file.name,
                        "content": content,
                        "file_size": file_size,
                        "path": md_file.relative_to(project_dir)
                    }

                    plans_data[status]["files"].append(plan_info)
                    total_files += 1

                except Exception as e:
                    plan_info = {
                        "name": md_file.name,
                        "error": str(e),
                        "path": md_file.relative_to(project_dir)
                    }
                    plans_data[status]["files"].append(plan_info)

        # Convert to Plan objects
        plans = self.files_to_plans(plans_data)

        # Print the results
        self.pretty_print(plans_data, total_files)

        print(f"✅ Converted {len(plans)} files to Plan objects")

        return plans_data, plans

    def sync_plans(self) -> PlanLoadResult:
        """Load plans from files and sync them to database

        Returns:
            PlanLoadResult: Summary of the database loading operation
        """
        print("🔄 Syncing plans from files to database...")

        # Load files and convert to Plan objects
        plans_data, plans = self.load_files()

        # Load plans into database
        result = self.load_database(plans)

        # Print summary
        print("=" * 50)
        print("📊 SYNC SUMMARY:")
        print(f"   ✅ Loaded: {result.loaded_count} plans")
        print(f"   ⏭️  Skipped: {
              result.skipped_count} plans (already up-to-date)")
        print(f"   ❌ Errors: {result.error_count} plans")

        if result.errors:
            print("\n❌ ERRORS:")
            for error in result.errors:
                print(f"   - {error.filename}: {error.error_message}")

        print("=" * 50)

        return result

    def pretty_print(self, plans_data, total_files):
        """Pretty print the plans data to console"""

        print("Loading plans from disk...")
        print("=" * 50)

        for status, data in plans_data.items():
            # Handle directory errors
            if "error" in data:
                print(data["error"])
                continue

            files = data["files"]

            if files:
                print(f"\n{status.value.upper()} ({len(files)} files):")
                print("-" * 30)

                for plan_info in files:
                    if "error" in plan_info:
                        print(f"  ❌ Error reading {
                              plan_info['name']}: {plan_info['error']}")
                        print()
                    else:
                        print(f"  📄 {plan_info['name']}")
                        print(f"     Status: {status.value}")
                        print(f"     Size: {
                              plan_info['file_size']:,} characters")
                        print(f"     Path: {plan_info['path']}")
                        print()
            else:
                print(f"\n{status.value.upper()}: No files found")

        print("=" * 50)
        print(f"Total plans found: {total_files}")
        print("💡 Use sync_plans() to load these plans into the database")
