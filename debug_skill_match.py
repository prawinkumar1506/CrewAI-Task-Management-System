from app.models.sample_data import SampleUser, SampleUserTask
from app.utils.dsa_utils import filter_users_for_task

# Pick a task to debug
task = SampleUserTask.objects(task_id="T0005").first()
users = list(SampleUser.objects())

print(f"Task {task.task_id} Required Skills: {task.required_skills}\n")

results = filter_users_for_task(task, users)

print("=== Top 5 Candidates ===")
for idx, (user, score) in enumerate(results, 1):
    print(f"{idx}. {user.user_id} ({user.username}) - Score: {score}")
print("========================\n")
