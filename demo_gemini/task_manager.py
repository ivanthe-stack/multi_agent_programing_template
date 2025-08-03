#!/usr/bin/env python3

import sys
import argparse
from task_database import TaskDatabase

def main():
    parser = argparse.ArgumentParser(description='Multi-Agent Task Management System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add task command
    add_parser = subparsers.add_parser('add', help='Add a new task')
    add_parser.add_argument('agent', help='Agent identifier')
    add_parser.add_argument('description', help='Task description')
    add_parser.add_argument('--status', default='In Progress', help='Task status (default: In Progress)')
    
    # List tasks command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--agent', help='Filter by agent')
    list_parser.add_argument('--status', help='Filter by status')
    list_parser.add_argument('--format', choices=['table', 'markdown'], default='table', help='Output format')
    
    # Update task command
    update_parser = subparsers.add_parser('update', help='Update task status')
    update_parser.add_argument('task_id', type=int, help='Task ID')
    update_parser.add_argument('status', help='New status')
    
    # Delete task command
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('task_id', type=int, help='Task ID')
    
    # Goal commands
    goal_parser = subparsers.add_parser('goal', help='Goal management')
    goal_subparsers = goal_parser.add_subparsers(dest='goal_command')
    
    set_goal_parser = goal_subparsers.add_parser('set', help='Set current goal')
    set_goal_parser.add_argument('goal_text', help='Goal description')
    
    get_goal_parser = goal_subparsers.add_parser('get', help='Get current goal')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export tasks to markdown')
    export_parser.add_argument('--output', help='Output file (default: stdout)')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate tasks from comunication.md')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    db = TaskDatabase()
    
    if args.command == 'add':
        task_id = db.add_task(args.agent, args.description, args.status)
        print(f"Task added with ID: {task_id}")
    
    elif args.command == 'list':
        if args.agent:
            tasks = db.get_tasks_by_agent(args.agent)
        elif args.status:
            tasks = db.get_tasks_by_status(args.status)
        else:
            tasks = db.get_all_tasks()
        
        if args.format == 'table':
            print_tasks_table(tasks)
        else:
            print_tasks_markdown(tasks)
    
    elif args.command == 'update':
        success = db.update_task_status(args.task_id, args.status)
        if success:
            print(f"Task {args.task_id} updated to '{args.status}'")
        else:
            print(f"Task {args.task_id} not found")
    
    elif args.command == 'delete':
        success = db.delete_task(args.task_id)
        if success:
            print(f"Task {args.task_id} deleted")
        else:
            print(f"Task {args.task_id} not found")
    
    elif args.command == 'goal':
        if args.goal_command == 'set':
            db.set_goal(args.goal_text)
            print("Goal updated")
        elif args.goal_command == 'get':
            goal = db.get_current_goal()
            print(goal if goal else "No goal set")
    
    elif args.command == 'export':
        markdown = db.export_to_markdown()
        if args.output:
            with open(args.output, 'w') as f:
                f.write(markdown)
            print(f"Tasks exported to {args.output}")
        else:
            print(markdown)
    
    elif args.command == 'migrate':
        migrate_from_markdown(db)

def print_tasks_table(tasks):
    if not tasks:
        print("No tasks found.")
        return
    
    print(f"{'ID':<4} {'Agent':<12} {'Date':<12} {'Status':<15} {'Description'}")
    print("-" * 80)
    
    for task in tasks:
        desc = task['description'][:40] + "..." if len(task['description']) > 40 else task['description']
        print(f"{task['id']:<4} {task['agent']:<12} {task['timestamp']:<12} {task['status']:<15} {desc}")

def print_tasks_markdown(tasks):
    if not tasks:
        print("No tasks found.")
        return
    
    for task in tasks:
        print(f"<details>")
        print(f"<summary>{task['description']}</summary>")
        print()
        print(f"**Agent:** {task['agent']}")
        print(f"**Timestamp:** {task['timestamp']}")
        print(f"**Description:** {task['description']}")
        print(f"**Status:** {task['status']}")
        print()
        print("</details>")

def migrate_from_markdown(db):
    """Migrate existing tasks from comunication.md to database"""
    try:
        with open('comunication.md', 'r') as f:
            content = f.read()
        
        # Extract goal
        if '<goal>' in content and '</goal>' in content:
            goal_start = content.find('<goal>') + 6
            goal_end = content.find('</goal>')
            goal = content[goal_start:goal_end].strip()
            if goal:
                db.set_goal(goal)
                print(f"Migrated goal: {goal}")
        
        # Extract tasks (simplified parsing)
        import re
        task_pattern = r'<details>\s*<summary>(.*?)</summary>.*?\*\*Agent:\*\* (.*?)\n.*?\*\*Timestamp:\*\* (.*?)\n.*?\*\*Description:\*\* (.*?)\n.*?\*\*Status:\*\* (.*?)\n'
        matches = re.findall(task_pattern, content, re.DOTALL)
        
        migrated_count = 0
        for match in matches:
            summary, agent, timestamp, description, status = match
            agent = agent.strip()
            timestamp = timestamp.strip()
            description = description.strip()
            status = status.strip()
            
            db.add_task(agent, description, status)
            migrated_count += 1
        
        print(f"Migrated {migrated_count} tasks from comunication.md")
        
    except FileNotFoundError:
        print("comunication.md not found")
    except Exception as e:
        print(f"Error migrating tasks: {e}")

if __name__ == "__main__":
    main()