# app/agents/supervisor_agent.py
'''
from app.models.sample_data import SampleUserTask
from app.agents.task_assign import assign_task
from app.agents.task_reassign import reassign_task
from datetime import datetime, timedelta

def supervise():
    """Periodically checks and assigns/reassigns tasks."""
    # Check for unassigned pending tasks
    pending_tasks = SampleUserTask.objects(status='pending')
    for task in pending_tasks:
        assign_task(task.task_id)
    # Check for overdue in_progress tasks (due in less than 2 days)
    now = datetime.utcnow()
    overdue_tasks = SampleUserTask.objects(
        status='in_progress',
        due_date__lt=now + timedelta(days=2)
    )
    for task in overdue_tasks:
        # Reassign only if not reassigned in last 24 hours
        last_reassign = None
        for log in reversed(task.assignment_log):
            if log.get('action') == 'reassigned':
                last_reassign = log['timestamp']
                break
        if last_reassign and (now - last_reassign).total_seconds() < 86400:
            continue
        reassign_task(task.task_id)'''
# app/agents/supervisor_agent.py

from app.models.sample_data import SampleUserTask
from app.agents.task_assign import assign_task
from app.agents.task_reassign import reassign_task
from app.agents.rag_agent import retrieve_similar_tasks
from datetime import datetime, timedelta
from app.utils.task_utils import check_overdue_tasks

def supervise():
    check_overdue_tasks() #newly added 13.6
    """Periodically checks and assigns/reassigns tasks with RAG integration."""
    print("\n=== SUPERVISOR CYCLE STARTED ===")
    print(f"[{datetime.now().isoformat()}] Checking system status...")

    # Check for unassigned pending tasks
    pending_tasks = SampleUserTask.objects(status='pending')
    print(f"\n🔄 Found {len(pending_tasks)} pending tasks:")
    for task in pending_tasks:
        print(f"  - Assigning task {task.task_id} ({task.name})")
        result = assign_task(task.task_id)
        print(f"    ✅ Assignment result: {result.get('status', 'failed')}")

    # Check for overdue in_progress tasks
    now = datetime.utcnow()
    overdue_tasks = SampleUserTask.objects(
        status='in_progress',
        due_date__lt=now + timedelta(days=2)
    )
    print(f"\n⏰ Found {len(overdue_tasks)} overdue tasks:")

    for task in overdue_tasks:
        print(f"\n🔍 Analyzing task {task.task_id} ({task.name})")

        # Check last reassignment time
        last_reassign = next(
            (log['timestamp'] for log in reversed(task.assignment_log)
             if log.get('action') == 'reassigned'), None)

        if last_reassign and (now - last_reassign).total_seconds() < 86400:
            print("  ⏩ Skipping: Reassigned within last 24 hours")
            continue

        # RAG Integration
        print("  🔎 Querying RAG system for similar tasks...")
        similar_tasks = retrieve_similar_tasks(task, top_k=3)

        if similar_tasks:
            print(f"  📚 Found {len(similar_tasks)} historical matches:")
            for st in similar_tasks:
                print(f"    - {st['task_id']} (User: {st['user_id']}, Outcome: {st['outcome']})")
            rag_context = "\nHistorical context considered in reassignment"
        else:
            print("  ℹ️ No similar historical tasks found")
            rag_context = ""

        # Reassign with RAG context
        print(f"  🔄 Initiating reassignment for {task.task_id}")
        result = reassign_task(task.task_id, rag_context=rag_context)

        if result.get('status') == 'success':
            print(f"    ✅ Reassigned to {result['user_id']} via {result['method']}")
        else:
            print(f"    ❌ Reassignment failed: {result.get('error', 'Unknown error')}")

    print("\n=== SUPERVISOR CYCLE COMPLETED ===")
