from enum import Enum
from datetime import datetime

class TaskStatus(Enum):
    WAITING_DETAILS = "waiting_for_details"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING_CONFIRM = "waiting_for_confirmation"
    COMPLETED = "completed"
    PARTIAL = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskManager:
    def __init__(self):
        self.current = None
        self.history = []
    
    def start(self, intent, steps):
        self.current = {
            "intent": intent,
            "steps": steps,
            "status": TaskStatus.PLANNING,
            "completed": [],
            "started_at": datetime.now().isoformat()
        }
        return self.current
    
    def update(self, status, completed_step=None):
        if self.current:
            self.current["status"] = status
            if completed_step:
                self.current["completed"].append(completed_step)
    
    def cancel(self):
        if self.current:
            self.current["status"] = TaskStatus.CANCELLED
            self.history.append(self.current)
            self.current = None
            return True
        return False
