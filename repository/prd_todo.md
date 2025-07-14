## IMPORTANT: Do not take immediate planning action on these items just yet. This is a high level checklist for `plan_service.py`

## Take the first todo checklist item and build a plan and do not work on the rest of the todo items until I tell you to work on the next one. We will start with the first checklist item and build a specific plan for that and then you'll ask for approval and I will iterate with you on that plan and then we will build it.

- [ ] Build out a plan for`def create_plan(plan: Plan) -> CreatePlanResult` to take a new plan and write it to the database
- [ ] Build out a plan for`def udpate_plan(plan: Plan) -> UpdatePlanResult` to update a plan and handle versioning properly
- [ ] Build out a plan for`get_plan(plan_id: str) -> Plan:` to retrieve a plan from the database with the plan id which should be a uuid.
- [ ] Build out a plan for`get_plan(name: str) -> Option[Plan]:` to retrieve a plan from the database with the name of the plan (which should be unique because it comes from the file name and file names need to be unique)
- [ ] Build out a plan for`mark_completed(plan_name: str) -> UpdatePlanResult:` to mark a plan completed. 
- [ ] Build out a plan for `mark_approved(plan_name: str) -> UpdatePlanResult:` to mark a plan as approved for implementation.
