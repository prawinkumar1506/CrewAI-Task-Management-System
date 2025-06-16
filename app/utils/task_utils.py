from datetime import datetime, timedelta
from app.models.sample_data import SampleUser, SampleUserTask

# app/utils/task_utils.py
import logging

logging.basicConfig(level=logging.INFO)
def update_task_assignment(task_id: str, new_user_id: str,
                           new_due_date: datetime = None,
                           status: str = 'in_progress',
                           reason: str = 'assignment') -> str:
    try:
        # Validate task exists and is modifiable
        task = SampleUserTask.objects(task_id=task_id).first()
        if not task:
            return "Error: Task not found"
        if task.status == 'completed':
            return "Error: Cannot modify completed tasks"

        # Validate new user
        new_user = SampleUser.objects(user_id=new_user_id).first()
        if not new_user:
            return f"Error: User {new_user_id} not found"
        if new_user.availability_status != 'available':
            return f"Error: User {new_user_id} is {new_user.availability_status}"
        if new_user.current_ongoing_tasks >= new_user.max_concurrent_tasks:
            return f"Error: User {new_user_id} at capacity ({new_user.current_ongoing_tasks}/{new_user.max_concurrent_tasks})"

        # Validate status transition
        valid_transitions = {
            'pending': ['in_progress', 'reassigned'],
            'in_progress': ['completed', 'blocked', 'reassigned', 'in_progress'],  # Allow in_progress → in_progress
            'reassigned': ['in_progress', 'blocked'],
            'blocked': ['in_progress']
        }
        if status not in valid_transitions.get(task.status, []):
            return f"Error: Invalid status transition {task.status} → {status}"

        # Handle due date
        if new_due_date:
            if new_due_date < datetime.utcnow():
                return "Error: New due date cannot be in past"
        elif status == 'in_progress':
            new_due_date = datetime.utcnow() + timedelta(days=3)

        # Track if workload needs updating
        old_user_id = task.user_id
        old_status = task.status
        needs_workload_update = (
                old_user_id != new_user_id or
                (old_status != 'in_progress' and status == 'in_progress')
        )

        # Update task fields
        task.user_id = new_user_id
        task.status = status
        task.due_date = new_due_date

        if status == 'in_progress' and not task.started_at:
            task.started_at = datetime.utcnow()

        task.reassigned_count += 1
        task.add_log_entry('assigned' if not old_user_id else 'reassigned', {
            'from': old_user_id,
            'to': new_user_id,
            'due_date': str(task.due_date),
            'status': status,
            'reason': reason
        })
        task.save()

        # Update user workloads
        if old_user_id:
            old_user = SampleUser.objects(user_id=old_user_id).first()
            if old_user and old_user_id != new_user_id:
                old_user.current_ongoing_tasks = max(0, old_user.current_ongoing_tasks - 1)
                old_user.save()

        if needs_workload_update:
            new_user.current_ongoing_tasks += 1
            new_user.save()

        return f"Success: Task {task_id} assigned to {new_user_id}"

    except Exception as e:
        logging.error(f"Assignment failed: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

from datetime import datetime
from app.models.sample_data import SampleUserTask


def check_overdue_tasks():
    """Automatically reassign overdue tasks using CrewAI"""
    from app.agents.crewai_integration import TaskCrew
    crew = TaskCrew()
    overdue_tasks = SampleUserTask.objects(
        due_date__lt=datetime.utcnow(),
        status='in_progress'
    )

    print(f"\n🔍 Found {len(overdue_tasks)} overdue tasks")
    for task in overdue_tasks:
        print(f"🔄 Reassigning task {task.task_id}")
        result = crew.assign_task(task.task_id)
        print(f"   Result: {result.get('status', 'failed')}")

# In app/utils/task_utils.py

def complete_task(task_id: str) -> str:
    """Official task completion workflow"""
    task = SampleUserTask.objects(task_id=task_id).first()
    if not task:
        return "Task not found"

    if task.user_id:
        user = SampleUser.objects(user_id=task.user_id).first()
        if user:
            user.current_ongoing_tasks = max(0, user.current_ongoing_tasks - 1)
            user.save()

    task.mark_completed()
    return f"Task {task_id} marked completed"

#app/utils/task_utils.py
from datetime import datetime
from app.models.sample_data import SampleUserTask
import threading
import time
def auto_complete_tasks():
    """Background task to auto-complete overdue tasks"""
    while True:
        now = datetime.now()
        overdue = SampleUserTask.objects(
            due_date__lt=now,
            status__nin=['completed', 'failed']
        )

        for task in overdue:
            # Only handle final status changes here
            task.status = 'completed'   #if task.progress > 90 else 'failed'
            task.save()

        time.sleep(86400)  # Run daily

# Start background thread
threading.Thread(target=auto_complete_tasks, daemon=True).start()
