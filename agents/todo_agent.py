from __future__ import annotations

from typing import List, Dict, Any, Optional

from agents.base_agent import Agent


class TodoAgent(Agent):
    """Agent for managing simple to-do tasks using the MemoryManager."""

    def add_task(self, description: str, user_id: Optional[str] = None) -> str:
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available. Cannot add task.]"
        success = self.orchestrator.memory_manager.add_task(description, user_id=user_id)
        if success:
            uid = user_id if user_id else self.orchestrator.memory_manager.default_user_id
            return f"[Task added for user '{uid}']"
        return "[Error: Failed to add task.]"

    def list_tasks(self, user_id: Optional[str] = None, show_completed: bool = True) -> str:
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available. Cannot list tasks.]"
        tasks = self.orchestrator.memory_manager.list_tasks(user_id=user_id, show_completed=show_completed)
        uid = user_id if user_id else self.orchestrator.memory_manager.default_user_id
        if tasks is None:
            return f"[Error: Could not retrieve tasks for user '{uid}'.]"
        if not tasks:
            return f"[No tasks found for user '{uid}'.]"
        lines = []
        for t in tasks:
            status = "✓" if t["completed"] else " "
            lines.append(f"[{status}] {t['id']}: {t['description']}")
        return "\n".join(lines)

    def complete_task(self, task_id: int, user_id: Optional[str] = None) -> str:
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available. Cannot complete task.]"
        success = self.orchestrator.memory_manager.complete_task(task_id, user_id=user_id, completed=True)
        uid = user_id if user_id else self.orchestrator.memory_manager.default_user_id
        if success:
            return f"[Marked task {task_id} as done for user '{uid}'.]"
        return f"[Error: Task {task_id} not found for user '{uid}'.]"

    def delete_task(self, task_id: int, user_id: Optional[str] = None) -> str:
        if not (self.orchestrator and self.orchestrator.memory_manager):
            return "[Error: MemoryManager not available. Cannot delete task.]"
        success = self.orchestrator.memory_manager.delete_task(task_id, user_id=user_id)
        uid = user_id if user_id else self.orchestrator.memory_manager.default_user_id
        if success:
            return f"[Deleted task {task_id} for user '{uid}'.]"
        return f"[Error: Task {task_id} not found for user '{uid}'.]"

    def get_tool_json_schemas(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "add_task",
                "description": "Add a new to-do task for the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "Task description."},
                        "user_id": {"type": ["string", "null"], "description": "Optional user ID.", "default": None}
                    },
                    "required": ["description"]
                }
            },
            {
                "name": "list_tasks",
                "description": "List to-do tasks for the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": ["string", "null"], "description": "Optional user ID.", "default": None},
                        "show_completed": {"type": "boolean", "description": "Include completed tasks", "default": True}
                    },
                    "required": []
                }
            },
            {
                "name": "complete_task",
                "description": "Mark a task as completed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "ID of the task."},
                        "user_id": {"type": ["string", "null"], "description": "Optional user ID.", "default": None}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "delete_task",
                "description": "Delete a task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "ID of the task."},
                        "user_id": {"type": ["string", "null"], "description": "Optional user ID.", "default": None}
                    },
                    "required": ["task_id"]
                }
            }
        ]
