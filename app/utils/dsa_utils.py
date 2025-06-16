# app/utils/dsa_utils.py

import heapq

'''def filter_users_for_task(task, users):
    """
    Pre-filter users based on:
    - Required skills (at least one match)
    - Availability (status and current load)
    Returns: list of (user, match_score) sorted by match_score descending
    """
    candidates = []
    for user in users:
        # Skip if not available or overloaded
        if user.availability_status != 'available':
            continue
        if user.current_ongoing_tasks >= user.max_concurrent_tasks:
            continue
        # Calculate skill match score
        match_score = user.skill_match_score(task.required_skills)
        if match_score > 0:  # At least one skill matches
            # We use a min-heap for top 5, so we store negative score
            candidates.append((-match_score, user))
    # Get top 5 by match_score (highest first)
    heapq.heapify(candidates)
    top_candidates = []
    for _ in range(min(5, len(candidates))):
        if candidates:
            score, user = heapq.heappop(candidates)
            top_candidates.append((user, -score))
    return top_candidates'''
# # app/utils/dsa_utils.py
# import heapq
# import logging
# from app.models.sample_data import SampleUser




# import heapq

# # app/utils/dsa_utils.py
# import heapq

# def skill_match_score(user_skills, required_skills):
#     """Calculate match score based on skill presence and level adequacy"""
#     if not required_skills:
#         return 0

#     matched_skills = 0
#     level_adequacy = 0.0

#     for skill, req_level in required_skills.items():
#         user_level = user_skills.get(skill, 0)
#         if user_level > 0:  # Skill exists
#             matched_skills += 1
#             if user_level >= req_level:
#                 level_adequacy += 1.0
#             else:
#                 level_adequacy += user_level / req_level

#     # Prioritize number of matched skills first
#     return (matched_skills * 1000) + (level_adequacy * 100)

# def filter_users_for_task(task, users):

#     """Return top 5 users with most relevant skills"""
#     print("\n=== DEBUG: Task Assignment ===")
#     print(f"Task {task.task_id} requires: {task.required_skills}\n")

#     candidates = []
#     for user in users:
#         score = skill_match_score(user.skills, task.required_skills)
#         print(f"User {user.user_id} skills: {user.skills}")
#         print(f"Score: {score}\n")
#         if score > 0:
#             heapq.heappush(candidates, (-score, user.user_id, user))

#     # Get top 5
#     top5 = [ (user, -score) for score, _, user in heapq.nsmallest(5, candidates) ]

#     print("=== Top 3 Candidates ===")
#     for idx, (user, score) in enumerate(top5, 1):
#         print(f"{idx}. {user.user_id} - Score: {score}")
#     print("========================")

#     return top5

# def get_workload_sorted_users(users):
#     """
#     Return users sorted by current workload (ascending) for load balancing.
#     """
#     workload_heap = []
#     for user in users:
#         # Use current load percentage
#         load_percent = (user.current_ongoing_tasks / user.max_concurrent_tasks) * 100
#         heapq.heappush(workload_heap, (load_percent, user))
#     sorted_users = []
#     while workload_heap:
#         load, user = heapq.heappop(workload_heap)
#         sorted_users.append(user)
#     return sorted_users


# app/utils/dsa_utils.py
import heapq
import logging
from app.models.sample_data import SampleUser

logger = logging.getLogger(__name__)

def skill_match_score(user_skills, required_skills):
    """Calculate skill match score with level adequacy"""
    if not required_skills:
        return 0

    matched_skills = 0
    level_adequacy = 0.0

    for skill, req_level in required_skills.items():
        user_level = user_skills.get(skill, 0)
        if user_level > 0:  # Skill exists
            matched_skills += 1
            level_adequacy += min(user_level / req_level, 1.0)

    # Weighted score: 70% skill match, 30% level adequacy
    return (matched_skills * 70) + (level_adequacy * 30)

def filter_users_for_task(task, users):
    """Return top 5 available users with relevant skills and capacity"""
    logger.info(f"\n=== Filtering candidates for task {task.task_id} ===")
    logger.info(f"Required skills: {task.required_skills}")

    candidates = []
    for user in users:
        # Skip unavailable users or those at capacity
        if user.availability_status != 'available':
            continue
        if user.current_ongoing_tasks >= user.max_concurrent_tasks:
            continue

        score = skill_match_score(user.skills, task.required_skills)
        if score > 0:
            # Use negative score for min-heap behavior
            heapq.heappush(candidates, (-score, user.user_id, user))

    # Extract top 5 candidates
    top_candidates = []
    while candidates and len(top_candidates) < 5:
        score, _, user = heapq.heappop(candidates)
        top_candidates.append((user, -score))

    logger.info("=== Top Candidates ===")
    for idx, (user, score) in enumerate(top_candidates, 1):
        logger.info(f"{idx}. {user.user_id} - Score: {score}")
    logger.info("======================")

    return top_candidates

def get_workload_sorted_users(users):
    """Return users sorted by current workload (ascending)"""
    workload_heap = []
    for user in users:
        if user.max_concurrent_tasks == 0:
            continue  # Prevent division by zero
        load_percent = (user.current_ongoing_tasks / user.max_concurrent_tasks) * 100
        heapq.heappush(workload_heap, (load_percent, user))
    
    return [user for _, user in heapq.nsmallest(len(workload_heap), workload_heap)]
