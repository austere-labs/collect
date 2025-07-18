import sqlite3
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from .plan_models import (
    PlanStatus, Plan, PlanData, PlanLoadResult, LoadError, PlanCreateResult)

# Import datetime adapters to ensure they're registered
from . import datetime_adapters  # noqa: F401


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

    def check_exists(self, plan_id: str) -> bool:
        """Check if a plan with the given ID already exists

        Args:
            plan_id: The plan ID to check

        Returns:
            bool: True if plan exists, False otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM plans WHERE id = ?", (plan_id,))
        return cursor.fetchone() is not None

    def create_new_plan(
            self,
            plan: Plan,
            change_summary: str = "Initial plan creation") -> PlanCreateResult:
        """Create a new plan and initialize version history

        Args:
            plan: Plan object to create
            change_summary: Description of this change
            (default: "Initial plan creation")

        Returns:
            PlanCreateResult: Success/failure with details
        """
        cursor = self.conn.cursor()

        try:
            # Check if plan ID already exists
            if self.check_exists(plan.id):
                return PlanCreateResult(
                    success=False,
                    plan_id=plan.id,
                    version=plan.version,
                    error_message=f"Plan with ID '{plan.id}' already exists",
                    error_type="DuplicateError"
                )

            # Serialize PlanData to JSON for JSONB storage
            plan_data_json = plan.data.model_dump_json()

            # Insert new plan into plans table
            cursor.execute("""
                INSERT INTO plans (
                id, name, data, version, content_hash, created_at, updated_at
                )
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

            # Insert initial version into plan_history table
            cursor.execute("""
                INSERT INTO plan_history (
                    id,
                    version,
                    data,
                    content_hash,
                    created_at,
                    archived_at,
                    change_summary
                )
                VALUES (?, ?, jsonb(?), ?, ?, ?, ?)
            """, (
                plan.id,
                plan.version,
                plan_data_json,
                plan.content_hash,
                plan.created_at,
                datetime.now(),  # archived_at is current time for new plans
                change_summary
            ))

            # Commit the transaction
            self.conn.commit()

            return PlanCreateResult(
                success=True,
                plan_id=plan.id,
                version=plan.version
            )

        except Exception as e:
            # Rollback transaction on any error
            self.conn.rollback()

            return PlanCreateResult(
                success=False,
                plan_id=plan.id,
                version=plan.version,
                error_message=str(e),
                error_type=type(e).__name__
            )

    def extract_description(self, content: str) -> Optional[str]:
        """Extract description from markdown content

        Looks for:
        1. ## Overview or ## Description section
        2. First paragraph after # title
        """
        lines = content.split('\n')

        # Look for Overview or Description section
        in_overview = False
        description_lines = []

        for i, line in enumerate(lines):
            if re.match(r'^##\s+(Overview|Description)', line, re.IGNORECASE):
                in_overview = True
                continue
            elif in_overview and line.strip().startswith('#'):
                # Hit another section
                break
            elif in_overview and line.strip():
                description_lines.append(line.strip())

        if description_lines:
            return ' '.join(description_lines[:3])  # First 3 lines max

        # Fallback: get first non-title paragraph
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                return line.strip()[:200]  # Max 200 chars

        return None

    def extract_tags(self, content: str, status: PlanStatus) -> List[str]:
        """Extract tags from markdown content

        Looks for:
        1. Tags in frontmatter
        2. ## Tags section
        3. Keywords from content
        """
        tags = [status.value]  # Always include status as a tag

        # Look for tags section
        lines = content.split('\n')
        in_tags = False

        for line in lines:
            if re.match(r'^##\s+Tags', line, re.IGNORECASE):
                in_tags = True
                continue
            elif in_tags and line.strip().startswith('#'):
                break
            elif in_tags and line.strip():
                # Parse comma or bullet-separated tags
                if line.strip().startswith('-'):
                    tags.append(line.strip()[1:].strip().lower())
                else:
                    for tag in re.split(r'[,;]', line):
                        tag = tag.strip().lower()
                        if tag and tag not in tags:
                            tags.append(tag)

        # Extract some keywords from title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).lower()
            # Extract action words
            for word in ['add', 'fix', 'implement', 'create', 'update', 'improve']:
                if word in title and word not in tags:
                    tags.append(word)

        return tags[:10]  # Limit to 10 tags

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

                    # Extract metadata from content
                    content = file_info["content"]
                    description = self.extract_description(content)
                    tags = self.extract_tags(content, status)

                    # Create PlanData object
                    plan_data = PlanData(
                        status=status,
                        markdown_content=content,
                        description=description,
                        tags=tags,
                        metadata={
                            "file_size": file_info["file_size"],
                            "original_path": str(file_info["path"]),
                            "filename": file_info["name"]
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
                needs_update = self.check_exists(plan.id)

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
                    cursor.execute(
                        """
                            INSERT INTO plans (
                            id,
                            name,
                            data,
                            version,
                            content_hash,
                            created_at,
                            updated_at)
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

    def load_files(self) -> tuple[dict[PlanStatus, dict],
                                  List[Plan],
                                  List[LoadError]]:
        """Read and display all plans from _docs/plans directory structure

        Returns:
            tuple[dict[PlanStatus, dict], List[Plan], List[LoadError]]:
                - Plans data organized by status
                - List of Plan objects
                - List of LoadError objects for any errors encountered
        """

        project_dir = Path(__file__).parent.parent
        plans_dir = project_dir / "_docs" / "plans"

        # Map directory names to PlanStatus enum values
        status_mapping = {
            "drafts": PlanStatus.DRAFT,
            "approved": PlanStatus.APPROVED,
            "completed": PlanStatus.COMPLETED
        }

        # Collect plan data
        plans_data: dict[PlanStatus, dict] = {}
        total_files: int = 0
        errors: List[LoadError] = []

        # Iterate through each status directory
        for dir_name, status in status_mapping.items():
            status_dir = plans_dir / dir_name

            if not status_dir.exists():
                plans_data[status] = {
                    "error": f"Directory not found: {status_dir}", "files": []}
                errors.append(LoadError(
                    filename=str(status_dir),
                    error_message=f"Directory not found: {status_dir}",
                    error_type="DirectoryNotFound"
                ))
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
                    errors.append(LoadError(
                        filename=md_file.name,
                        error_message=str(e),
                        error_type=type(e).__name__
                    ))

        # Convert to Plan objects
        plans = self.files_to_plans(plans_data)

        # Print the results
        self.pretty_print(plans_data, total_files)

        print(f"✅ Converted {len(plans)} files to Plan objects")

        return plans_data, plans, errors

    def sync_plans(self) -> PlanLoadResult:
        """Load plans from files and sync them to database

        Returns:
            PlanLoadResult: Summary of the database loading operation
        """
        print("🔄 Syncing plans from files to database...")

        # Load files and convert to Plan objects
        plans_data, plans, file_errors = self.load_files()

        # Load plans into database
        result = self.load_database(plans)

        # Merge file loading errors with database errors
        if file_errors:
            if result.errors:
                result.errors.extend(file_errors)
            else:
                result.errors = file_errors
            result.error_count += len(file_errors)

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
                print(
                    f"   - {error.filename}: {error.error_message} ({error.error_type})")

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
