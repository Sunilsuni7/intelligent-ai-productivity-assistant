from typing import List, Optional, Any
from pydantic import BaseModel, Field

class Goal(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    target_date: Optional[str] = None
    priority: str = "medium"
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PlanTask(BaseModel):
    id: Optional[int] = None
    milestone_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    estimated_minutes: int = 60
    due_date: Optional[str] = None
    status: str = "pending"
    order_index: int = 0
    dependencies: List[int] = Field(default_factory=list) # List of task_ids this depends on

class Milestone(BaseModel):
    id: Optional[int] = None
    plan_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    order_index: int = 0
    target_date: Optional[str] = None
    status: str = "pending"
    tasks: List[PlanTask] = Field(default_factory=list)

class ProjectPlan(BaseModel):
    id: Optional[int] = None
    goal_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    milestones: List[Milestone] = Field(default_factory=list)

class TaskDependency(BaseModel):
    id: Optional[int] = None
    task_id: int
    depends_on_task_id: int
    dependency_type: str = "blocks"

class PlanProgress(BaseModel):
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    completion_percentage: float = 0.0

class PlanningSuggestion(BaseModel):
    type: str
    title: str
    reason: str
    related_task_id: Optional[int] = None
    suggested_action: str
    confidence: float = 1.0
