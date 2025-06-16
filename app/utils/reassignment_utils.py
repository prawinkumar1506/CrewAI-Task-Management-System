from datetime import datetime, timedelta
from app.models.sample_data import SampleUserTask
from app.utils.task_utils import update_task_assignment


def reassign_task(task_id: str, new_user_id: str = None,
                  new_due_days: int = None,
                  reason: str = 'manual_reassignment'):
    """
    Manual reassignment by admin
    """
    task = SampleUserTask.objects(task_id=task_id).first()
    if not task:
        return "Task not found"

    new_due_date = datetime.utcnow() + timedelta(days=new_due_days) if new_due_days else None

    if new_user_id:
        # Reassign to specific user
        return update_task_assignment(
            task_id=task_id,
            new_user_id=new_user_id,
            new_due_date=new_due_date,
            status='in_progress'
        )
    else:
        # Auto-reassign using existing logic
        return update_task_assignment(
            task_id=task_id,
            new_user_id=crew.assign_task(task_id),
            new_due_date=new_due_date,
            status='reassigned'
        )
