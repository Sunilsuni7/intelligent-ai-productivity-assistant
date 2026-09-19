from typing import List, Optional
from pydantic import BaseModel

class TaskMetrics(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    completion_rate: float = 0.0
    overdue_rate: float = 0.0

class PriorityBreakdown(BaseModel):
    high_total: int = 0
    high_completed: int = 0
    medium_total: int = 0
    medium_completed: int = 0
    low_total: int = 0
    low_completed: int = 0

class GoalProgress(BaseModel):
    goal_id: int
    title: str
    progress_percentage: float = 0.0
    completed_tasks: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    milestone_progress: float = 0.0

class ProjectProgress(BaseModel):
    plan_id: int
    title: str
    overall_completion: float = 0.0
    completed_tasks: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    milestones_completed: int = 0
    milestones_remaining: int = 0

class ReminderMetrics(BaseModel):
    total: int = 0
    completed: int = 0
    pending: int = 0
    overdue: int = 0

class ProductivityInsight(BaseModel):
    type: str  # positive, negative, info
    title: str
    explanation: str
    severity: str = "low"
    confidence: float = 1.0

class ProductivitySummary(BaseModel):
    tasks: TaskMetrics = TaskMetrics()
    priorities: PriorityBreakdown = PriorityBreakdown()
    active_goals_count: int = 0
    active_projects_count: int = 0
    completed_milestones_count: int = 0
    pending_milestones_count: int = 0
    reminders: ReminderMetrics = ReminderMetrics()
    insights: List[ProductivityInsight] = []
    productivity_score: float = 0.0
