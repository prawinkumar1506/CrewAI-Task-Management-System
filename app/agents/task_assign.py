# app/agents/task_assign.py

from app.models.sample_data import SampleUser, SampleUserTask
from app.utils.dsa_utils import filter_users_for_task
from app.agents.mistral_llm import query_mistral_llm
from app.agents.rag_agent import retrieve_similar_tasks
from config import RAG_ENABLED
from datetime import datetime
import time
import json

def assign_task(task_id, force_user_id=None):
    task = SampleUserTask.objects(task_id=task_id).first()
    if not task:
        return {"error": "Task not found"}
    if task.status != 'pending':
        return {"error": f"Task is not pending (current status: {task.status})"}
    if force_user_id:
        # Forced assignment logic
        user = SampleUser.objects(user_id=force_user_id).first()
        if not user:
            return {"error": "User not found"}
        if user.availability_status != 'available':
            return {"error": f"User {user.username} is not available"}
        if user.current_ongoing_tasks >= user.max_concurrent_tasks:
            return {"error": f"User {user.username} is at max capacity"}
        return finalize_assignment(task, user, "forced")
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
    # RAG: Retrieve similar tasks
    rag_context = ""
    if RAG_ENABLED:
        similar_tasks = retrieve_similar_tasks(task, top_k=3)
        if similar_tasks:
            rag_context = "\nSimilar historical tasks:\n"
            for t in similar_tasks:
                rag_context += f"- Task {t['task_id']} assigned to {t['user_id']}: {t['document'][:200]}...\n"
    # LLM prompt
    prompt = f"""Task Assignment Analysis:
Task: {task.name} ({task.task_id})
Required Skills: {json.dumps(task.required_skills)}
Priority: {task.priority}
Due: {task.due_date.strftime('%Y-%m-%d')}
Type: {task.task_type}
Candidates (with match scores):
{json.dumps(candidate_info, indent=2)}
{rag_context}
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
        return finalize_assignment(task, user, "llm_recommended", result["reason"], candidate_info, processing_time)
    except Exception as e:
        # Fallback: choose candidate with highest match score
        best_candidate = max(candidates, key=lambda x: x[1])
        user = best_candidate[0]
        reason = f"Algorithmic fallback - Highest match score: {best_candidate[1]}"
        return finalize_assignment(task, user, "algorithmic", reason, candidate_info, processing_time)

def finalize_assignment(task, user, method, reason="", candidates=None, processing_time=0):
    """Assign task to user and update logs."""
    task.user_id = user.user_id
    task.status = 'in_progress'
    task.started_at = datetime.utcnow()
    user.current_ongoing_tasks += 1
    user.save()
    task.add_log_entry("assigned", {
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
    }
