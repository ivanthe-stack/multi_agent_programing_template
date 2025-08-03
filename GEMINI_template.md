## Communication
- Task management is now handled through the SQLite database system.
- Use `task_manager.py` for task operations:
  - Add tasks: `python task_manager.py add "Agent Name" "Description"`
  - List tasks: `python task_manager.py list`
  - Update status: `python task_manager.py update <id> "Status"`
- For legacy markdown format: `python task_manager.py export`
- Goals are managed separately - agents cannot modify the main goal

## Example Flow
1. Any agent can initiate a task or send a message to another agent, always including its identifier in the message.
2. Agents process received messages and may respond or forward information as needed.
3. The process is fully decentralized and can involve any number of agents.

---
don`t stop until you are stoped or the goal is finished and tested add new task if there are no
_See `comunication.md` for up-to-date communication records and further details on agent interactions._
