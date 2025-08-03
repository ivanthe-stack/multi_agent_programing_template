You are agent $ARGUMENTS. 

Always log your tasks using the database system:
- Add new tasks: `python task_manager.py add "Agent $ARGUMENTS" "task description"`
- Update progress: `python task_manager.py update <task_id> "In Progress"`
- Mark complete: `python task_manager.py update <task_id> "Done"`
- List tasks: `python task_manager.py list`

Before starting implementation:
- Add each task only once to the database
- Break tasks into small pieces focused on architecture and code updates
- Include which files will be modified in the description

While working:
- Keep task status updated in the database
- Never delete tasks from the database

When finished:
- Change status to "Done" in the database