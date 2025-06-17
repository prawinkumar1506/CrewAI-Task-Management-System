import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Callable, Any, Dict, List
from datetime import datetime, timedelta
import queue
import time
from dataclasses import dataclass
from enum import Enum

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class BackgroundTask:
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    created_at: datetime
    max_retries: int = 3
    retry_count: int = 0
    result: Any = None
    error: str = None
    completed: bool = False

class AsyncProcessor:
    def __init__(self, max_workers: int = 4, max_process_workers: int = 2):
        """Initialize async processor with thread and process pools"""
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_process_workers)
        self.task_queue = queue.PriorityQueue()
        self.running_tasks: Dict[str, BackgroundTask] = {}
        self.completed_tasks: Dict[str, BackgroundTask] = {}
        self.running = False
        self.worker_thread = None
        
    def start(self):
        """Start the background task processor"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
            self.worker_thread.start()
            print("🔄 Async processor started")
    
    def stop(self):
        """Stop the background task processor"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        print("🛑 Async processor stopped")
    
    def submit_task(self, func: Callable, *args, priority: TaskPriority = TaskPriority.NORMAL, 
                   use_process: bool = False, **kwargs) -> str:
        """Submit a task for background processing"""
        task_id = f"task_{int(time.time() * 1000)}"
        task = BackgroundTask(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            created_at=datetime.now(),
            use_process=use_process
        )
        
        # Add to priority queue (lower number = higher priority)
        self.task_queue.put((priority.value, task))
        self.running_tasks[task_id] = task
        return task_id
    
    def _process_tasks(self):
        """Main task processing loop"""
        while self.running:
            try:
                # Get next task from queue
                if not self.task_queue.empty():
                    priority, task = self.task_queue.get(timeout=1)
                    
                    # Execute task
                    if task.use_process:
                        future = self.process_pool.submit(task.func, *task.args, **task.kwargs)
                    else:
                        future = self.thread_pool.submit(task.func, *task.args, **task.kwargs)
                    
                    # Handle result
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout
                        task.result = result
                        task.completed = True
                    except Exception as e:
                        task.error = str(e)
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            # Re-queue with lower priority
                            task.priority = TaskPriority(max(1, task.priority.value - 1))
                            self.task_queue.put((task.priority.value, task))
                        else:
                            task.completed = True
                    
                    # Move to completed tasks
                    if task.completed:
                        self.completed_tasks[task.id] = task
                        if task.id in self.running_tasks:
                            del self.running_tasks[task.id]
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in task processor: {e}")
                time.sleep(1)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task"""
        task = self.running_tasks.get(task_id) or self.completed_tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        return {
            "id": task.id,
            "completed": task.completed,
            "result": task.result,
            "error": task.error,
            "retry_count": task.retry_count,
            "created_at": task.created_at.isoformat(),
            "priority": task.priority.name
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        return {
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "queue_size": self.task_queue.qsize(),
            "thread_pool_active": len(self.thread_pool._threads),
            "process_pool_active": len(self.process_pool._processes)
        }
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        tasks_to_remove = [
            task_id for task_id, task in self.completed_tasks.items()
            if task.created_at < cutoff_time
        ]
        for task_id in tasks_to_remove:
            del self.completed_tasks[task_id]
        return len(tasks_to_remove)

# Global async processor instance
async_processor = AsyncProcessor()

def background_task(priority: TaskPriority = TaskPriority.NORMAL, use_process: bool = False):
    """Decorator to run function as background task"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            task_id = async_processor.submit_task(func, *args, priority=priority, use_process=use_process, **kwargs)
            return {"task_id": task_id, "status": "submitted"}
        return wrapper
    return decorator 