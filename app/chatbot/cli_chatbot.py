# app/chatbot/cli_chatbot.py
from datetime import datetime, timedelta
from app.models.sample_data import SampleUser, SampleUserTask
from app.agents.crewai_integration import TaskCrew
from app.agents.rag_agent import RAGSystem
from app.utils.task_utils import check_overdue_tasks
import json
import os

class TaskCLI:
    def __init__(self):
        self.crew = TaskCrew()
        self.rag = RAGSystem()
        self.running = True

    def start(self):
        print("🚀 Task Management System 2.0")
        self._main_loop()

    def _main_loop(self):
        while self.running:
            print("\n===== Main Menu =====")
            print("1. Assign Task\n2. Reassign Task\n3. Create Task\n4. Create User")
            print("5. List Users\n6. List Tasks\n7. Edit User\n8. Edit Task")
            print("9. Supervise\n10. System Status\n11. Exit")
            choice = input("Choice (1-11): ")

            try:
                {
                    '1': self._assign_task,
                    '2': self._reassign_task,
                    '3': self._create_task,
                    '4': self._create_user,
                    '5': self._list_users,
                    '6': self._list_tasks,
                    '7': self._edit_user,
                    '8': self._edit_task,
                    '9': self._supervise,
                    '10': self._system_status,
                    '11': self._exit
                }[choice]()
            except KeyError:
                print("Invalid choice!")

    def _assign_task(self):
        task_id = input("Enter task ID: ")
        result = self.crew.assign_task(task_id)
        print(f"\nAssignment Result: {result}")

    def _reassign_task(self):
        task_id = input("Enter task ID: ")
        new_user = input("New user ID (leave empty for auto): ")
        if new_user:
            result = self.crew.assign_task(task_id, force_user=new_user)
        else:
            result = self.crew.assign_task(task_id)
        print(f"\nReassignment Result: {result}")

    def _create_task(self):
        print("\n🆕 Create New Task")
        task = SampleUserTask(
            task_id=f"T{datetime.now().strftime('%Y%m%d%H%M')}",
            name=input("Task name: "),
            required_skills=json.loads(input("Required skills (JSON): ")),
            priority=input("Priority (low/medium/high): "),
            due_date=datetime.now() + timedelta(days=int(input("Due in days: "))),
            task_type=input("Task type: ")
        )
        task.save()
        print(f"Created task {task.task_id}")

    def _create_user(self):
        print("\n👤 Create New User")
        user = SampleUser(
            user_id=f"U{datetime.now().strftime('%Y%m%d%H%M')}",
            username=input("Username: "),
            skills=json.loads(input("Skills (JSON): ")),
            max_concurrent_tasks=int(input("Max tasks: ")),
            availability_status='available'
        )
        user.save()
        print(f"Created user {user.user_id}")

    def _list_users(self):
        """Enhanced: show full availability info, experience level, and last active"""
        print("\n=== Users ===")
        print(f"{'ID':<6} {'Username':<20} {'Availability':<15} {'Workload':<10} {'Experience':<10} {'Last Active':<20}")
        print("-" * 90)
        for user in SampleUser.objects():
            # Emoji for availability
            if user.availability_status == 'available':
                status_icon = "✅"
            elif user.availability_status == 'busy':
                status_icon = "⏳"
            elif user.availability_status == 'on_leave':
                status_icon = "🌴"
            else:
                status_icon = "❓"

            workload = f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}"
            last_active = user.last_active.strftime("%Y-%m-%d %H:%M:%S") if user.last_active else "N/A"
            availability = f"{status_icon} {user.availability_status}"
            print(f"{user.user_id:<6} {user.username[:19]:<20} {availability:<15} {workload:<10} {user.experience_level:<10} {last_active:<20}")

    def _list_tasks(self):
        """Enhanced: show status emoji + text, priority, type, progress"""
        print("\n=== Tasks ===")
        print(f"{'ID':<6} {'Name':<25} {'Status':<15} {'Assigned To':<12} {'Due Date':<12} {'Type':<12} {'Priority':<8} {'Progress':<10}")
        print("-" * 110)
        for task in SampleUserTask.objects():
            # Emoji for task status
            if task.status == 'pending':
                status_icon = "🕒"
            elif task.status == 'in_progress':
                status_icon = "⚙️"
            elif task.status == 'completed':
                status_icon = "✅"
            elif task.status == 'blocked':
                status_icon = "⛔"
            else:
                status_icon = "❓"

            assigned = task.user_id if task.user_id else "Unassigned"
            due_date = task.due_date.strftime("%Y-%m-%d") if task.due_date else "N/A"
            status_display = f"{status_icon} {task.status}"
            progress = f"{task.progress:.1f}%"

            #print(f"{task.task_id:<6} {task.name[:24]:<25} {status_display:<15} {assigned:<12} {due_date:<12} {task.task_type:<12} {task.priority:<8} {progress:<10}")
            print(
                f"{task.task_id:<6} "
                f"{task.name[:24]:<25} "
                f"{status_display:<15} "
                f"{assigned:<12} "
                f"{due_date:<12} "
                f"{(task.task_type or 'N/A'):<12} "
                f"{(task.priority or 'N/A'):<8} "
                f"{progress:<10}"
            )

    def _edit_user(self):
        """Enhanced user editing with deletion option"""
        print("\n✏️ Edit User")
        user_id = input("Enter user ID to edit: ")
        user = SampleUser.objects(user_id=user_id).first()

        if not user:
            print(f"❌ User {user_id} not found")
            return

        print(f"\nCurrent user: {user.username}")
        print("1. Edit specific field\n2. Edit all fields\n3. Delete user")
        choice = input("Choice (1-3): ")

        if choice == '1':
            self._edit_user_field(user)
        elif choice == '2':
            self._edit_all_user_fields(user)
        elif choice == '3':
            self._delete_user(user)
        else:
            print("Invalid choice")

    def _edit_user_field(self, user):
        """Edit specific user field"""
        print("\nFields to edit:")
        print("1. Username\n2. Skills\n3. Max concurrent tasks\n4. Availability status")
        field_choice = input("Choice (1-4): ")

        if field_choice == '1':
            user.username = input(f"New username (current: {user.username}): ")
        elif field_choice == '2':
            user.skills = json.loads(input(f"New skills JSON (current: {user.skills}): "))
        elif field_choice == '3':
            user.max_concurrent_tasks = int(input(f"New max tasks (current: {user.max_concurrent_tasks}): "))
        elif field_choice == '4':
            user.availability_status = input(f"New status (current: {user.availability_status}): ")

        user.save()
        print(f"✅ User {user.user_id} updated successfully")

    def _edit_all_user_fields(self, user):
        """Edit all user fields"""
        user.username = input(f"Username (current: {user.username}): ") or user.username
        skills_input = input(f"Skills JSON (current: {user.skills}): ")
        if skills_input:
            user.skills = json.loads(skills_input)

        max_tasks_input = input(f"Max concurrent tasks (current: {user.max_concurrent_tasks}): ")
        if max_tasks_input:
            user.max_concurrent_tasks = int(max_tasks_input)

        status_input = input(f"Availability status (current: {user.availability_status}): ")
        if status_input:
            user.availability_status = status_input

        user.save()
        print(f"✅ User {user.user_id} updated successfully")

    def _delete_user(self, user):
        """Delete user with confirmation"""
        confirm = input(f"⚠️ Delete user {user.username} ({user.user_id})? (yes/no): ")
        if confirm.lower() == 'yes':
            user.delete()
            print(f"🗑️ User {user.user_id} deleted successfully")
        else:
            print("Deletion cancelled")

    def _edit_task(self):
        """Enhanced task editing with completion tracking"""
        print("\n✏️ Edit Task")
        task_id = input("Enter task ID to edit: ")
        task = SampleUserTask.objects(task_id=task_id).first()

        if not task:
            print(f"❌ Task {task_id} not found")
            return

        print(f"\nCurrent task: {task.name}")
        print("1. Edit specific field\n2. Edit all fields\n3. Delete task")
        choice = input("Choice (1-3): ")

        if choice == '1':
            self._edit_task_field(task)
        elif choice == '2':
            self._edit_all_task_fields(task)
        elif choice == '3':
            self._delete_task(task)
        else:
            print("Invalid choice")

    def _edit_task_field(self, task):
        """Edit specific task field with completion tracking"""
        print("\nFields to edit:")
        print("1. Name\n2. Status\n3. Priority\n4. Due date\n5. Required skills\n6. Assigned user")
        field_choice = input("Choice (1-6): ")

        old_status = task.status

        if field_choice == '1':
            task.name = input(f"New name (current: {task.name}): ")
        elif field_choice == '2':
            task.status = input(f"New status (current: {task.status}): ")
        elif field_choice == '3':
            task.priority = input(f"New priority (current: {task.priority}): ")
        elif field_choice == '4':
            days = int(input("Due in how many days from now: "))
            task.due_date = datetime.now() + timedelta(days=days)
        elif field_choice == '5':
            task.required_skills = json.loads(input(f"New skills JSON (current: {task.required_skills}): "))
        elif field_choice == '6':
            task.user_id = input(f"New assigned user (current: {task.user_id}): ")

        # Handle completion status change
        if old_status != 'completed' and task.status == 'completed':
            self._handle_task_completion(task)

        task.save()
        print(f"✅ Task {task.task_id} updated successfully")

    def _edit_all_task_fields(self, task):
        """Edit all task fields"""
        old_status = task.status

        task.name = input(f"Name (current: {task.name}): ") or task.name
        task.status = input(f"Status (current: {task.status}): ") or task.status
        task.priority = input(f"Priority (current: {task.priority}): ") or task.priority

        due_input = input("Due in how many days from now (leave empty to keep current): ")
        if due_input:
            task.due_date = datetime.now() + timedelta(days=int(due_input))

        skills_input = input(f"Required skills JSON (current: {task.required_skills}): ")
        if skills_input:
            task.required_skills = json.loads(skills_input)

        user_input = input(f"Assigned user (current: {task.user_id}): ")
        if user_input:
            task.user_id = user_input

        # Handle completion status change
        if old_status != 'completed' and task.status == 'completed':
            self._handle_task_completion(task)

        task.save()
        print(f"✅ Task {task.task_id} updated successfully")

    def _handle_task_completion(self, task):
        """Handle task completion and update task history"""
        task.completed_at = datetime.now()

        # Update RAG system with completed task
        self.rag.index_completed_tasks()

        # Update task_history.json
        self._update_task_history_file(task)

        # Free up user capacity
        if task.user_id:
            user = SampleUser.objects(user_id=task.user_id).first()
            if user:
                user.current_ongoing_tasks = max(0, user.current_ongoing_tasks - 1)
                user.save()

        print(f"📝 Task {task.task_id} marked as completed and added to history")

    def _update_task_history_file(self, task):
        """Update task_history.json with completed task"""
        history_file = "app/data/task_history.json"

        # Load existing history
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        # Add new completed task
        task_record = {
            "task_id": task.task_id,
            "name": task.name,
            "user_id": task.user_id,
            "required_skills": task.required_skills,
            "outcome": "success",
            "completed_at": task.completed_at.isoformat() if task.completed_at else datetime.now().isoformat(),
            "duration": (task.completed_at - task.started_at).days if task.started_at and task.completed_at else 0
        }

        history.append(task_record)

        # Save updated history
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

    def _delete_task(self, task):
        """Delete task with confirmation"""
        confirm = input(f"⚠️ Delete task {task.name} ({task.task_id})? (yes/no): ")
        if confirm.lower() == 'yes':
            # Free up user capacity if task was assigned
            if task.user_id and task.status == 'in_progress':
                user = SampleUser.objects(user_id=task.user_id).first()
                if user:
                    user.current_ongoing_tasks = max(0, user.current_ongoing_tasks - 1)
                    user.save()

            task.delete()
            print(f"🗑️ Task {task.task_id} deleted successfully")
        else:
            print("Deletion cancelled")

    def _supervise(self):
        """Enhanced supervision with detailed reporting"""
        print("\n🔍 Supervising System...")

        # Check overdue tasks
        print("Checking overdue tasks...")
        check_overdue_tasks()

        # System health checks
        total_users = SampleUser.objects.count()
        available_users = SampleUser.objects(availability_status='available').count()
        total_tasks = SampleUserTask.objects.count()
        pending_tasks = SampleUserTask.objects(status='pending').count()
        in_progress_tasks = SampleUserTask.objects(status='in_progress').count()
        completed_tasks = SampleUserTask.objects(status='completed').count()

        print(f"\n📊 System Overview:")
        print(f"Users: {available_users}/{total_users} available")
        print(f"Tasks: {pending_tasks} pending, {in_progress_tasks} in progress, {completed_tasks} completed")

        # Check for workload imbalances
        overloaded_users = []
        underutilized_users = []

        for user in SampleUser.objects(availability_status='available'):
            utilization = user.current_ongoing_tasks / user.max_concurrent_tasks
            if utilization >= 0.9:
                overloaded_users.append(user)
            elif utilization <= 0.3:
                underutilized_users.append(user)

        if overloaded_users:
            print(f"\n⚠️ Overloaded users ({len(overloaded_users)}):")
            for user in overloaded_users:
                print(f"  - {user.username} ({user.current_ongoing_tasks}/{user.max_concurrent_tasks})")

        if underutilized_users:
            print(f"\n💡 Underutilized users ({len(underutilized_users)}):")
            for user in underutilized_users:
                print(f"  - {user.username} ({user.current_ongoing_tasks}/{user.max_concurrent_tasks})")

        # Auto-assign pending tasks
        if pending_tasks > 0:
            print(f"\n🔄 Auto-assigning {pending_tasks} pending tasks...")
            for task in SampleUserTask.objects(status='pending'):
                try:
                    result = self.crew.assign_task(task.task_id)
                    print(f"  ✅ {task.task_id}: {result}")
                    # print("hi")
                except Exception as e:
                    print(f"  ❌ {task.task_id}: Failed - {str(e)}")

    def _system_status(self):
        self.rag.index_completed_tasks()
        check_overdue_tasks()
        print("\nSystem Status:")
        print(f"Users: {SampleUser.objects.count()}")
        print(f"Tasks: {SampleUserTask.objects.count()}")
        print(f"Completed Tasks: {self.rag.collection.count()}")

    def _exit(self):
        self.running = False
        print("Goodbye!")

if __name__ == "__main__":
    cli = TaskCLI()
    cli.start()

