import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List
from .plan_models import PlanStatus, Plan, PlanData


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
        print("TODO: build PlanLoadResult and save to database")
