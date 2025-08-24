import marimo

__generated_with = "0.14.12"
app = marimo.App(width="medium")


@app.cell
def _():
    # Import tools with alias, ensuring we get the local package
    import sys
    from pathlib import Path
    
    # Add project root to the FRONT of sys.path to prioritize local packages
    project_root = Path(__file__).parent.parent
    project_root_str = str(project_root.resolve())
    
    # Remove any existing entries first to avoid duplicates
    if project_root_str in sys.path:
        sys.path.remove(project_root_str)
    
    # Insert at the beginning so it takes priority
    sys.path.insert(0, project_root_str)
    
    # Clear any cached imports
    if 'tools' in sys.modules:
        del sys.modules['tools']
    if 'tools.loader' in sys.modules:
        del sys.modules['tools.loader']
    
    # Now import the local tools package
    import tools as mytools
    
    print(f"Imported tools from: {mytools.__file__ if hasattr(mytools, '__file__') else 'unknown'}")
    print(f"Has loader attribute: {hasattr(mytools, 'loader')}")
    
    return (mytools,)


@app.cell
def _(mytools):
    # Test loading plans from disk
    plans_data = mytools.loader.load_plans_from_disk()
    print(f"Project: {plans_data['project_name']}")
    print(f"GitHub URL: {plans_data['github_url']}")
    print(f"Found {len(plans_data['plans'])} plans")
    print(f"Found {len(plans_data['errors'])} errors")

    return (plans_data,)


@app.cell
def _(plans_data):
    # Display plan details
    import json
    print("Plans data structure:")
    print(json.dumps({
        "project_name": plans_data["project_name"],
        "github_url": plans_data["github_url"],
        "plan_count": len(plans_data["plans"]),
        "error_count": len(plans_data["errors"]),
        "sample_plan": plans_data["plans"][0] if plans_data["plans"] else None
    }, indent=2))
    return


if __name__ == "__main__":
    app.run()
