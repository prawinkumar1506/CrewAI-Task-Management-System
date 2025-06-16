# app/models/sample_data.py

from mongoengine import connect, Document, StringField, DictField, IntField, DateTimeField, FloatField, ListField
from datetime import datetime, timedelta
from datetime import datetime, timezone
import random
# In SampleUserTask model's mark_completed() method:

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

MONGODB_CONN_STR = "mongodb+srv://prawin2310095:zmbzpjc186ub3WAS@taskmgmt.ad7exfr.mongodb.net/taskmgmt?retryWrites=true&w=majority"
DB_NAME = "taskmgmt"
# RAG and LLM settings
RAG_ENABLED = True
TASK_HISTORY_COLLECTION = "task_history"
MISTRAL_MODEL_PATH = "./models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"


# Connect to MongoDB
connect(db=DB_NAME, host=MONGODB_CONN_STR,uuidRepresentation='standard',tz_aware=True)

# ======================
# Data Models
# ======================
class SampleUser(Document):
    meta = {'collection': 'sample_users'}
    user_id = StringField(required=True, unique=True)
    username = StringField(required=True)
    skills = DictField()  # {"python": 8, "react": 6}
    max_concurrent_tasks = IntField(default=5)
    current_ongoing_tasks = IntField(default=0)
    availability_status = StringField(choices=['available', 'busy', 'on_leave'], default='available')
    experience_level = StringField(choices=['junior', 'mid', 'senior'], default=random.choice(['junior', 'mid', 'senior']))
    preferred_task_types = ListField(StringField())
    last_active = DateTimeField(default=datetime.now(timezone.utc))



    def skill_match_score(self,user_skills, required_skills):
        """Calculate match score based on skill presence and level adequacy"""
        if not required_skills:
            return 0

        matched_skills = 0
        level_adequacy = 0.0

        for skill, req_level in required_skills.items():
            user_level = user_skills.get(skill, 0)
            if user_level > 0:  # Skill exists
                matched_skills += 1
                if user_level >= req_level:
                    level_adequacy += 1.0
                else:
                    level_adequacy += user_level / req_level

        # Prioritize number of matched skills first
        return (matched_skills * 1000) + (level_adequacy * 100)




class SampleUserTask(Document):
    meta = {'collection': 'sample_user_tasks'}
    task_id = StringField(required=True, unique=True)
    user_id = StringField()
    name = StringField(required=True)
    status = StringField(choices=['pending', 'in_progress', 'completed', 'blocked'], default='pending')
    required_skills = DictField()  # {"python": 7, "ml": 6}
    priority = StringField(choices=['low', 'medium', 'high'], default=random.choice(['low', 'medium', 'high']))
    due_date = DateTimeField()
    task_type = StringField(choices=['feature', 'bug', 'research', 'documentation', 'testing'])
    estimated_effort_hours = FloatField()
    actual_effort_hours = FloatField(default=0.0)
    created_at = DateTimeField(default=datetime.now(timezone.utc))
    started_at = DateTimeField()
    completed_at = DateTimeField()
    reassigned_count = IntField(default=0)
    assignment_log = ListField(DictField())
    progress = FloatField(default=0.0)

    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)
        self.save()

    def add_log_entry(self, action, details):
        self.assignment_log.append({
            "timestamp": datetime.now(timezone.utc),
            "action": action,
            "details": details
        })
        self.save()
    def update_status_based_on_due_date(self):
        """Auto-update status based on due date"""
        if self.due_date < datetime.now(timezone.utc):
            if self.status not in ['completed', 'blocked']:
                self.status = 'overdue'
                self.add_log_entry('status_change', {
                    'from': self.status,
                    'to': 'overdue',
                    'reason': 'deadline_passed'
                })
                self.save()

    def mark_completed(self):
        # Only process if NOT already completed
        if self.status != 'completed':
            user = SampleUser.objects(user_id=self.user_id).first()
            if user:
                # Reduce workload count
                user.current_ongoing_tasks = max(0, user.current_ongoing_tasks - 1)
                user.save()

            # Update task status and timestamp
            self.status = 'completed'
            self.completed_at = datetime.now(timezone.utc)
            self.add_log_entry('completed', {'details': 'Task finalized'})
            self.save()
            from app.agents.rag_agent import index_task_history
            index_task_history()

def populate_sample_data():
    # Clear existing data
    SampleUser.drop_collection()
    SampleUserTask.drop_collection()

    # Skill domains for predictable matching
    skill_domains = {
        'frontend': {'javascript': 9, 'react': 8, 'typescript': 7},
        'backend': {'python': 9, 'nodejs': 8, 'mongodb': 7},
        'devops': {'docker': 9, 'kubernetes': 8, 'aws': 7},
        'data': {'python': 8, 'machine_learning': 9, 'pytorch': 7},
        'mobile': {'swift': 8, 'kotlin': 7, 'flutter': 6},
        'qa': {'selenium': 8, 'cypress': 7, 'postman': 6}
    }

    # Initial users with current_ongoing_tasks = 0 (will update later)
    users = [
        SampleUser(user_id="U0001", username="Frontend Lead", skills=skill_domains['frontend'],
                   availability_status='available', max_concurrent_tasks=4, current_ongoing_tasks=0),
        SampleUser(user_id="U0002", username="Backend Expert", skills=skill_domains['backend'],
                   availability_status='available', max_concurrent_tasks=3, current_ongoing_tasks=0),
        SampleUser(user_id="U0003", username="DevOps Master", skills=skill_domains['devops'],
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0004", username="Data Scientist", skills=skill_domains['data'],
                   availability_status='available', max_concurrent_tasks=3, current_ongoing_tasks=0),
        SampleUser(user_id="U0005", username="Mobile Dev", skills=skill_domains['mobile'],
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0006", username="QA Lead", skills=skill_domains['qa'],
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0007", username="Full Stack",
                   skills={**skill_domains['frontend'], **skill_domains['backend']},
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0008", username="Cloud Engineer", skills=skill_domains['devops'],
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),

        # Busy Users (30%)
        SampleUser(user_id="U0009", username="Backend Dev", skills=skill_domains['backend'],
                   availability_status='busy', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0010", username="Data Engineer", skills=skill_domains['data'],
                   availability_status='busy', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0011", username="Mobile Expert", skills=skill_domains['mobile'],
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0012", username="QA Engineer", skills=skill_domains['qa'],
                   availability_status='busy', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0013", username="Frontend Dev", skills=skill_domains['frontend'],
                   availability_status='busy', max_concurrent_tasks=5, current_ongoing_tasks=0),

        # On Leave Users (20%)
        SampleUser(user_id="U0014", username="DevOps Jr", skills=skill_domains['devops'],
                   availability_status='on_leave', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0015", username="Data Analyst", skills=skill_domains['data'],
                   availability_status='on_leave', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0016", username="Mobile Jr", skills=skill_domains['mobile'],
                   availability_status='on_leave', max_concurrent_tasks=5, current_ongoing_tasks=0),

        # Edge Cases
        SampleUser(user_id="U0017", username="Overloaded Dev", skills=skill_domains['backend'],
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0018", username="New Hire", skills=skill_domains['frontend'],
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0019", username="Part-time QA", skills=skill_domains['qa'],
                   availability_status='available', max_concurrent_tasks=5, current_ongoing_tasks=0),
        SampleUser(user_id="U0020", username="Architect",
                   skills={**skill_domains['backend'], **skill_domains['devops']},
                   availability_status='busy', max_concurrent_tasks=5, current_ongoing_tasks=0)
    ]

    # Save users
    for user in users:
        user.save()

    # Define task data
    tasks_data = [
        {'name': 'React Migration', 'skills': skill_domains['frontend'], 'status': 'pending'},
        {'name': 'API Gateway', 'skills': skill_domains['backend'], 'status': 'pending'},
        {'name': 'CI/CD Pipeline', 'skills': skill_domains['devops'], 'status': 'pending'},
        {'name': 'Data Model Update', 'skills': skill_domains['data'], 'status': 'pending'},
        {'name': 'Mobile Auth', 'skills': skill_domains['mobile'], 'status': 'pending'},
        {'name': 'E2E Testing', 'skills': skill_domains['qa'], 'status': 'pending'},
        {'name': 'Dashboard Redesign', 'skills': skill_domains['frontend'], 'status': 'in_progress', 'user': 'U0001', 'due': 3},
        {'name': 'Microservices Refactor', 'skills': skill_domains['backend'], 'status': 'in_progress', 'user': 'U0002', 'due': 5},
        {'name': 'K8s Cluster Setup', 'skills': skill_domains['devops'], 'status': 'in_progress', 'user': 'U0003', 'due': 7},
        {'name': 'ML Model Training', 'skills': skill_domains['data'], 'status': 'in_progress', 'user': 'U0004', 'due': 10},
        {'name': 'iOS Offline Mode', 'skills': skill_domains['mobile'], 'status': 'in_progress', 'user': 'U0005', 'due': 4},
        {'name': 'Performance Testing', 'skills': skill_domains['qa'], 'status': 'in_progress', 'user': 'U0006', 'due': 2},
        {'name': 'Auth Service', 'skills': skill_domains['backend'], 'status': 'in_progress', 'user': 'U0007', 'due': 6},
        {'name': 'Cloud Migration', 'skills': skill_domains['devops'], 'status': 'in_progress', 'user': 'U0008', 'due': 14},
        {'name': 'UI Component Lib', 'skills': skill_domains['frontend'], 'status': 'completed', 'user': 'U0001', 'due': -5},
        {'name': 'Database Optimization', 'skills': skill_domains['backend'], 'status': 'completed', 'user': 'U0002', 'due': -10},
        {'name': 'Monitoring Setup', 'skills': skill_domains['devops'], 'status': 'completed', 'user': 'U0003', 'due': -7},
        {'name': 'Legacy System Patch', 'skills': skill_domains['backend'], 'status': 'in_progress', 'user': 'U0009', 'due': -3},
        {'name': 'Mobile Crash Fix', 'skills': skill_domains['mobile'], 'status': 'in_progress', 'user': 'U0011', 'due': -2},
        {'name': 'Load Testing', 'skills': skill_domains['qa'], 'status': 'in_progress', 'user': 'U0019', 'due': 1},
        {'name': 'Architecture Review', 'skills': {**skill_domains['backend'], **skill_domains['devops']},
         'status': 'in_progress', 'user': 'U0020', 'due': 7}
    ]

    base_date =datetime.now(timezone.utc)

    # Track user task counts
    user_task_count = {}

    for idx, task_info in enumerate(tasks_data):
        task_id = f"T{idx+1:04d}"
        task = SampleUserTask(
            task_id=task_id,
            name=task_info['name'],
            required_skills=task_info['skills'],
            due_date=base_date + timedelta(days=task_info.get('due', 7)),
            task_type='feature',
            estimated_effort_hours=random.uniform(8.0, 40.0),
            status=task_info['status']
        )

        if 'user' in task_info:
            user = SampleUser.objects(user_id=task_info['user']).first()
            if user:
                task.user_id = user.user_id
                if task.status == 'in_progress':
                    user_task_count[user.user_id] = user_task_count.get(user.user_id, 0) + 1

        task.save()

        if task.status == 'completed':
            task.mark_completed()
            task.completed_at = base_date - timedelta(days=abs(task_info['due']))
            task.save()

    # Update users' current_ongoing_tasks after task creation
    for user_id, count in user_task_count.items():
        user = SampleUser.objects(user_id=user_id).first()
        if user:
            user.current_ongoing_tasks = count
            user.save()

    print("Sample data created successfully with task-user consistency.")



if __name__ == "__main__":
    populate_sample_data()
    # Create sample task
    # try:
    #     from app.agents.crewai_integration import TaskCrew
    #
    #     # Create sample task
    #     task = SampleUserTask(
    #         task_id="T0001",
    #         name="Mobile Auth",
    #         required_skills={"python": 8, "security": 7},
    #         status="pending"
    #     ).save()
    #
    #     # Test assignment
    #     crew = TaskCrew()
    #     result = crew.assign_task("T0001")
    #     print("Task assignment result:", result)
    # except ImportError as e:
    #     print(f"Warning: Could not import TaskCrew ({e}). Skipping task assignment test.")
    # except Exception as e:
    #     print(f"Error during task assignment test: {e}")