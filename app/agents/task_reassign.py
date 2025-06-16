# app/agents/task_reassign.py
'''
from app.models.sample_data import SampleUser, SampleUserTask
from app.utils.dsa_utils import filter_users_for_task
from app.agents.mistral_llm import query_mistral_llm
from datetime import datetime, timedelta
import time
import json

def reassign_task(task_id, force_user_id=None):
    task = SampleUserTask.objects(task_id=task_id).first()
    if not task:
        return {"error": "Task not found"}
    if task.status != 'in_progress':
        return {"error": f"Task is not in_progress (current status: {task.status})"}
    if force_user_id:
        # Forced reassignment logic
        user = SampleUser.objects(user_id=force_user_id).first()
        if not user:
            return {"error": "User not found"}
        if user.availability_status != 'available':
            return {"error": f"User {user.username} is not available"}
        if user.current_ongoing_tasks >= user.max_concurrent_tasks:
            return {"error": f"User {user.username} is at max capacity"}
        return finalize_reassignment(task, user, "forced")
    # Pre-filter candidates using DSA
    all_users = SampleUser.objects()
    candidates = filter_users_for_task(task, all_users)
    if not candidates:
        return {"error": "No available users found with required skills"}
    # Prepare candidate info for LLM
    candidate_info = []
    for user, match_score in candidates:
        candidate_info.append({
            "user_id": user.user_id,
            "username": user.username,
            "skills": user.skills,
            "current_load": f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}",
            "experience": user.experience_level,
            "match_score": match_score
        })
    # LLM prompt
    prompt = f"""Task Reassignment Analysis:
Task: {task.name} ({task.task_id})
Required Skills: {json.dumps(task.required_skills)}
Priority: {task.priority}
Due: {task.due_date.strftime('%Y-%m-%d')}
Type: {task.task_type}
Candidates (with match scores):
{json.dumps(candidate_info, indent=2)}
Recommend the best user for this task based on:
- Skill match (most important)
- Current workload (lower is better)
- Experience level (senior for high priority)
- Task type and user preferences
Response format: {{ "user_id": "U1001", "reason": "Detailed explanation..." }}
"""
    start_time = time.time()
    llm_response = query_mistral_llm(prompt)
    processing_time = time.time() - start_time
    try:
        result = json.loads(llm_response)
        user = SampleUser.objects(user_id=result["user_id"]).first()
        if not user:
            return {"error": "LLM recommended user not found"}
        return finalize_reassignment(task, user, "llm_recommended", result["reason"], candidate_info, processing_time)
    except Exception as e:
        # Fallback: choose candidate with highest match score
        best_candidate = max(candidates, key=lambda x: x[1])
        user = best_candidate[0]
        reason = f"Algorithmic fallback - Highest match score: {best_candidate[1]}"
        return finalize_reassignment(task, user, "algorithmic", reason, candidate_info, processing_time)

def finalize_reassignment(task, user, method, reason="", candidates=None, processing_time=0):
    """Reassign task to user and update logs."""
    old_user = SampleUser.objects(user_id=task.user_id).first()
    if old_user:
        old_user.current_ongoing_tasks -= 1
        old_user.save()
    task.user_id = user.user_id
    task.status = 'in_progress'
    task.reassigned_count += 1
    user.current_ongoing_tasks += 1
    user.save()
    task.add_log_entry("reassigned", {
        "method": method,
        "reason": reason,
        "processing_time": processing_time,
        "candidates": candidates
    })
    task.save()
    return {
        "status": "success",
        "user_id": user.user_id,
        "task_id": task.task_id,
        "reason": reason,
        "method": method
    }'''

# # app/agents/task_reassign.py

# from app.models.sample_data import SampleUser, SampleUserTask
# from app.utils.dsa_utils import filter_users_for_task
# from app.agents.mistral_llm import query_mistral_llm
# from app.agents.rag_agent import retrieve_similar_tasks
# from datetime import datetime, timedelta
# import time
# import json

# def reassign_task(task_id, force_user_id=None,new_due_days=None, rag_context=""):
#     print(f"\n♻️ INITIATING REASSIGNMENT FOR TASK {task_id}")
#     task = SampleUserTask.objects(task_id=task_id).first()

#     if not task:
#         print("❌ Error: Task not found")
#         return {"error": "Task not found"}

#     print(f"📋 Task Details: {task.name} (Priority: {task.priority})")

#     if task.status != 'in_progress':
#         print(f"⚠️ Invalid status for reassignment: {task.status}")
#         return {"error": f"Task is not in_progress (current status: {task.status})"}

#     # Retrieve RAG context if not provided
#     if not rag_context:
#         print("🔍 Fetching RAG context...")
#         similar_tasks = retrieve_similar_tasks(task, top_k=3)
#         rag_context = format_rag_context(similar_tasks)

#     if force_user_id:
#         # Handle due date update
#         if new_due_days:
#             new_due_date = datetime.utcnow() + timedelta(days=new_due_days)
#             task.due_date = new_due_date
#             print(f"📅 New due date set to {new_due_date.strftime('%Y-%m-%d')}")

#         return handle_manual_reassignment(task, force_user_id, rag_context)

#     print("🤖 Starting automated reassignment process")
#     return handle_auto_reassignment(task, rag_context)

# def handle_manual_reassignment(task, user_id, rag_context):
#     user = SampleUser.objects(user_id=user_id).first()
#     if not user:
#         print(f"❌ User {user_id} not found")
#         return {"error": "User not found"}

#     print(f"🔍 Validating user {user_id} ({user.username})")

#     # RAG-based validation
#     if rag_context:
#         print("  ✅ RAG context available for validation")
#         similar_users = {t['user_id'] for t in rag_context.get('similar_tasks', [])}
#         if user_id not in similar_users:
#             print(f"  ⚠️ Warning: User {user_id} has no history with similar tasks")

#     # Existing validation logic
#     if user.availability_status != 'available':
#         print(f"  ❌ User {user.username} is not available")
#         return {"error": f"User {user.username} is not available"}

#     return finalize_reassignment(task, user, "manual", "Admin override", rag_context)

# def handle_auto_reassignment(task, rag_context):
#     print("🔧 Filtering candidates with DSA...")
#     candidates = filter_users_for_task(task, SampleUser.objects())

#     if not candidates:
#         print("❌ No qualified candidates found")
#         return {"error": "No available users found with required skills"}

#     print(f"👥 Found {len(candidates)} potential candidates")

#     # Prepare LLM input with RAG context
#     prompt = build_llm_prompt(task, candidates, rag_context)

#     print("🧠 Querying LLM with RAG-enhanced context...")
#     start_time = time.time()
#     llm_response = query_mistral_llm(prompt, task)
#     processing_time = time.time() - start_time

#     try:
#         result = json.loads(llm_response)
#         print(f"  ✅ LLM recommendation: {result['user_id']}")
#         user = SampleUser.objects(user_id=result["user_id"]).first()
#         return finalize_reassignment(task, user, "llm+rag", result["reason"],
#                                      rag_context, processing_time)
#     except Exception as e:
#         print(f"⚠️ LLM parse error: {str(e)}")
#         print("🔄 Falling back to algorithmic selection")
#         best_candidate = max(candidates, key=lambda x: x[1])
#         return finalize_reassignment(task, best_candidate[0], "algorithmic",
#                                      "Fallback to highest match score",
#                                      rag_context, processing_time)

# def build_llm_prompt(task, candidates, rag_context):
#     candidate_info = [{
#         "user_id": user.user_id,
#         "skills": user.skills,
#         "workload": f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}",
#         "success_rate": calculate_user_success_rate(user.user_id, rag_context)
#     } for user, _ in candidates]

#     return f"""Task Reassignment Analysis:
# Task: {task.name} ({task.task_id})
# Required Skills: {json.dumps(task.required_skills)}
# Current Assignee: {task.user_id}
# RAG Context: {json.dumps(rag_context, indent=2)}
# Candidates: {json.dumps(candidate_info, indent=2)}
# Recommendation Criteria:
# 1. Skill match with task requirements
# 2. Current workload capacity
# 3. Historical success rate with similar tasks
# 4. Task priority ({task.priority}) considerations
# Response format: {{ "user_id": "U1001", "reason": "Detailed explanation..." }}"""

# def finalize_reassignment(task, user, method, reason, rag_context, processing_time=0):
#     print(f"🔨 Finalizing reassignment to {user.user_id} ({method})")
#     """Update due date if provided"""
#     if hasattr(task, 'new_due_date'):  # If coming from manual reassignment
#         task.due_date = task.new_due_date
#         del task.new_due_date
#     # Update previous user
#     if old_user := SampleUser.objects(user_id=task.user_id).first():
#         old_user.current_ongoing_tasks -= 1
#         old_user.save()
#         print(f"  🔓 Freed capacity for {old_user.user_id}")

#     # Update new user
#     user.current_ongoing_tasks += 1
#     user.save()
#     print(f"  🔒 Updated workload for {user.user_id}: {user.current_ongoing_tasks}")

#     # Update task
#     task.user_id = user.user_id
#     task.reassigned_count += 1
#     task.add_log_entry("reassigned", {
#         "method": method,
#         "reason": f"{reason} | RAG: {bool(rag_context)}",
#         "processing_time": processing_time,
#         "rag_context": rag_context
#     })
#     task.save()

#     print(f"✅ Successfully reassigned {task.task_id} to {user.user_id}")
#     return {
#         "status": "success",
#         "user_id": user.user_id,
#         "method": method,
#         "processing_time": f"{processing_time:.2f}s"
#     }

# def format_rag_context(similar_tasks):
#     if not similar_tasks:
#         return {"similar_tasks": [], "success_rate": 0}

#     success_count = sum(1 for t in similar_tasks if t['outcome'] == 'success')
#     return {
#         "similar_tasks": [{
#             "task_id": t['task_id'],
#             "user_id": t['user_id'],
#             "outcome": t['outcome'],
#             "duration": t['duration']
#         } for t in similar_tasks],
#         "success_rate": f"{(success_count/len(similar_tasks))*100:.1f}%"
#     }

# def calculate_user_success_rate(user_id, rag_context):
#     if not rag_context.get('similar_tasks'):
#         return "N/A"

#     user_tasks = [t for t in rag_context['similar_tasks'] if t['user_id'] == user_id]
#     if not user_tasks:
#         return "No history"

#     success_count = sum(1 for t in user_tasks if t['outcome'] == 'success')
#     return f"{(success_count/len(user_tasks))*100:.1f}%"

# app/agents/task_reassign.py
from app.models.sample_data import SampleUser, SampleUserTask
from app.utils.dsa_utils import filter_users_for_task
from app.agents.mistral_llm import query_mistral_llm
from app.agents.rag_agent import retrieve_similar_tasks
from datetime import datetime, timedelta
import time
import json
import logging

logger = logging.getLogger(__name__)

def reassign_task(task_id, force_user_id=None, new_due_days=None, rag_context=""):
    """Reassign a task either manually or automatically with RAG context"""
    try:
        task = SampleUserTask.objects(task_id=task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"error": "Task not found"}

        logger.info(f"♻️ Reassigning task {task_id} ({task.name})")
        
        if task.status != 'in_progress':
            logger.error(f"Invalid status for reassignment: {task.status}")
            return {"error": f"Task is not in_progress (current status: {task.status})"}

        # Retrieve RAG context if not provided
        if not rag_context:
            logger.info("🔍 Fetching RAG context...")
            similar_tasks = retrieve_similar_tasks(task, top_k=3)
            rag_context = format_rag_context(similar_tasks)

        # Handle manual vs auto reassignment
        if force_user_id:
            return handle_manual_reassignment(task, force_user_id, rag_context, new_due_days)
        else:
            return handle_auto_reassignment(task, rag_context)

    except Exception as e:
        logger.error(f"Reassignment failed: {str(e)}", exc_info=True)
        return {"error": str(e)}

def handle_manual_reassignment(task, user_id, rag_context, new_due_days):
    """Handle manual reassignment with validation"""
    try:
        user = SampleUser.objects(user_id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        logger.info(f"🔍 Validating user {user_id} ({user.username})")

        # Validate user capacity
        if user.availability_status != 'available':
            raise ValueError(f"User {user.username} is not available")
        if user.current_ongoing_tasks >= user.max_concurrent_tasks:
            raise ValueError(f"User {user.username} is at max capacity")

        # Update due date if provided
        if new_due_days:
            new_due_date = datetime.utcnow() + timedelta(days=new_due_days)
            task.due_date = new_due_date
            logger.info(f"📅 New due date set to {new_due_date.strftime('%Y-%m-%d')}")

        # RAG-based validation
        if rag_context:
            similar_users = {t['user_id'] for t in rag_context.get('similar_tasks', [])}
            if user_id not in similar_users:
                logger.warning(f"⚠️ User {user_id} has no history with similar tasks")

        return finalize_reassignment(task, user, "manual", "Admin override", rag_context)

    except Exception as e:
        logger.error(f"Manual reassignment failed: {str(e)}")
        return {"error": str(e)}

def handle_auto_reassignment(task, rag_context):
    """Handle automated reassignment with RAG and LLM"""
    try:
        logger.info("🤖 Starting automated reassignment process")
        candidates = filter_users_for_task(task, SampleUser.objects())
        
        if not candidates:
            raise ValueError("No qualified candidates found")

        logger.info(f"👥 Found {len(candidates)} potential candidates")

        # Prepare and execute LLM request
        prompt = build_llm_prompt(task, candidates, rag_context)
        start_time = time.time()
        llm_response = query_mistral_llm(prompt, task)
        processing_time = time.time() - start_time

        try:
            result = json.loads(llm_response)
            user = SampleUser.objects(user_id=result["user_id"]).first()
            if not user:
                raise ValueError("LLM recommended user not found")
                
            logger.info(f"✅ LLM recommendation: {user.user_id}")
            return finalize_reassignment(task, user, "llm+rag", 
                                       result["reason"], rag_context, processing_time)
            
        except Exception as e:
            logger.warning("🔄 Falling back to algorithmic selection")
            best_candidate = max(candidates, key=lambda x: x[1])
            return finalize_reassignment(task, best_candidate[0], "algorithmic",
                                       "Fallback to highest match score", rag_context, processing_time)

    except Exception as e:
        logger.error(f"Auto reassignment failed: {str(e)}")
        return {"error": str(e)}

def build_llm_prompt(task, candidates, rag_context):
    """Construct LLM prompt with RAG context"""
    candidate_info = [{
        "user_id": user.user_id,
        "skills": user.skills,
        "workload": f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}",
        "success_rate": calculate_user_success_rate(user.user_id, rag_context)
    } for user, _ in candidates]

    return f"""Task Reassignment Analysis:
Task: {task.name} ({task.task_id})
Required Skills: {json.dumps(task.required_skills)}
Current Assignee: {task.user_id}
RAG Context: {json.dumps(rag_context, indent=2)}
Candidates: {json.dumps(candidate_info, indent=2)}
Recommendation Criteria:
1. Skill match with task requirements
2. Current workload capacity
3. Historical success rate with similar tasks
4. Task priority ({task.priority}) considerations
Response format: {{ "user_id": "UXXXX", "reason": "Detailed explanation..." }}"""

def finalize_reassignment(task, user, method, reason, rag_context, processing_time=0):
    """Finalize the reassignment and update all records"""
    try:
        old_user_id = task.user_id
        old_user = SampleUser.objects(user_id=old_user_id).first()

        # Update user workloads first
        if old_user:
            old_user.current_ongoing_tasks = max(0, old_user.current_ongoing_tasks - 1)
            old_user.save()
            logger.info(f"🔓 Freed capacity for {old_user.user_id}")

        user.current_ongoing_tasks += 1
        user.save()
        logger.info(f"🔒 Updated workload for {user.user_id}: {user.current_ongoing_tasks}")

        # Update task record
        task.user_id = user.user_id
        task.reassigned_count += 1
        task.add_log_entry("reassigned", {
            "method": method,
            "reason": f"{reason} | RAG: {bool(rag_context)}",
            "processing_time": processing_time,
            "rag_context": rag_context
        })
        task.save()

        logger.info(f"✅ Successfully reassigned {task.task_id} to {user.user_id}")
        return {
            "status": "success",
            "user_id": user.user_id,
            "method": method,
            "processing_time": f"{processing_time:.2f}s"
        }

    except Exception as e:
        logger.error(f"Finalization failed: {str(e)}")
        raise

def format_rag_context(similar_tasks):
    """Format RAG results for LLM consumption"""
    if not similar_tasks:
        return {"similar_tasks": [], "success_rate": 0}

    success_count = sum(1 for t in similar_tasks if t.get('outcome') == 'success')
    return {
        "similar_tasks": [{
            "task_id": t.get('task_id'),
            "user_id": t.get('user_id'),
            "outcome": t.get('outcome', 'unknown'),
            "duration": t.get('duration', 0)
        } for t in similar_tasks],
        "success_rate": f"{(success_count/len(similar_tasks))*100:.1f}%"
    }

def calculate_user_success_rate(user_id, rag_context):
    """Calculate user's historical success rate"""
    if not rag_context.get('similar_tasks'):
        return "N/A"

    user_tasks = [t for t in rag_context['similar_tasks'] if t.get('user_id') == user_id]
    if not user_tasks:
        return "No history"

    success_count = sum(1 for t in user_tasks if t.get('outcome') == 'success')
    return f"{(success_count/len(user_tasks))*100:.1f}%"
