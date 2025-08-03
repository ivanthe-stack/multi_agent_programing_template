import sqlite3
import datetime
from typing import List, Dict, Optional
import json

class TaskDatabase:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'In Progress',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_task(self, agent: str, description: str, status: str = "In Progress") -> int:
        """Add a new task to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute('''
            INSERT INTO tasks (agent, timestamp, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (agent, timestamp, description, status, now, now))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """Update the status of a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE tasks SET status = ?, updated_at = ?
            WHERE id = ?
        ''', (status, now, task_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def update_task_description(self, task_id: int, description: str) -> bool:
        """Update the description of a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE tasks SET description = ?, updated_at = ?
            WHERE id = ?
        ''', (description, now, task_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def update_task_agent(self, task_id: int, agent: str) -> bool:
        """Update the agent of a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE tasks SET agent = ?, updated_at = ?
            WHERE id = ?
        ''', (agent, now, task_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, agent, timestamp, description, status, created_at, updated_at
            FROM tasks
            ORDER BY created_at DESC
        ''')
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'agent': row[1],
                'timestamp': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        conn.close()
        return tasks
    
    def get_tasks_by_agent(self, agent: str) -> List[Dict]:
        """Get all tasks for a specific agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, agent, timestamp, description, status, created_at, updated_at
            FROM tasks
            WHERE agent = ?
            ORDER BY created_at DESC
        ''', (agent,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'agent': row[1],
                'timestamp': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        conn.close()
        return tasks
    
    def get_tasks_by_status(self, status: str) -> List[Dict]:
        """Get all tasks with a specific status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, agent, timestamp, description, status, created_at, updated_at
            FROM tasks
            WHERE status = ?
            ORDER BY created_at DESC
        ''', (status,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'agent': row[1],
                'timestamp': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        conn.close()
        return tasks
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def set_goal(self, goal_text: str):
        """Set the current goal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Deactivate all previous goals
        cursor.execute('UPDATE goals SET is_active = 0')
        
        # Add new goal
        now = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO goals (goal_text, created_at, is_active)
            VALUES (?, ?, 1)
        ''', (goal_text, now))
        
        conn.commit()
        conn.close()
    
    def get_current_goal(self) -> Optional[str]:
        """Get the current active goal"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT goal_text FROM goals
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def export_to_markdown(self) -> str:
        """Export all tasks to markdown format"""
        goal = self.get_current_goal()
        tasks = self.get_all_tasks()
        
        markdown = f"<goal>\n{goal or 'No goal set'}\n</goal>\n\nTask Log:\n\n"
        
        for task in tasks:
            markdown += f"<details>\n<summary>{task['description']}</summary>\n\n"
            markdown += f"**Agent:** {task['agent']}\n"
            markdown += f"**Timestamp:** {task['timestamp']}\n"
            markdown += f"**Description:** {task['description']}\n"
            markdown += f"**Status:** {task['status']}\n\n"
            markdown += "</details>\n"
        
        return markdown

if __name__ == "__main__":
    # Example usage
    db = TaskDatabase()
    
    # Migrate existing tasks from comunication.md if needed
    print("Task database initialized successfully!")
    print(f"Database location: {db.db_path}")