from mongoengine import connect
from app.models import User

# Connect to your MongoDB
connect(
    db="taskmgmt",
    host="mongodb+srv://prawin2310095:zmbzpjc186ub3WAS@taskmgmt.ad7exfr.mongodb.net/taskmgmt?retryWrites=true&w=majority"
)
# Insert sample users
users = [
    {
        "user_id": "user_003",
        "name": "Charlie",
        "skills": ["HTML", "Figma", "CSS"],
        "current_tasks": [],
        "availability": 85.0
    },
    {
        "user_id": "user_004",
        "name": "Diana",
        "skills": ["React", "HTML", "Figma"],
        "current_tasks": [],
        "availability": 90.0
    }
]



for user_data in users:
    User(**user_data).save()
    print(f"Inserted user: {user_data['user_id']}")
