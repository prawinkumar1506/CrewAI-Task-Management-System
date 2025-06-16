#
# # app/agents/crewai_integration.py
# import logging
# import json
# import re
# import heapq
# from datetime import datetime
# from typing import List, Tuple
# from pydantic import BaseModel, Field
# from crewai import Agent, Task, Crew, Process, LLM
# from crewai.tools import tool
# from app.models.sample_data import SampleUser, SampleUserTask
# from app.utils.task_utils import update_task_assignment
#
# logging.basicConfig(level=logging.INFO)
#
# class AssignmentOutput(BaseModel):
#     user_id: str = Field(..., pattern=r'^U\d{4}$', example="U0001")
#     rationale: str = Field(..., min_length=20)
#
# def skill_match_score(user_skills, required_skills):
#     """Calculate match score based on skill presence and level adequacy"""
#     if not required_skills:
#         return 0
#
#     matched_skills = 0
#     level_adequacy = 0.0
#
#     for skill, req_level in required_skills.items():
#         user_level = user_skills.get(skill, 0)
#         if user_level > 0:  # Skill exists
#             matched_skills += 1
#             if user_level >= req_level:
#                 level_adequacy += 1.0
#             else:
#                 level_adequacy += user_level / req_level
#
#     # Prioritize number of matched skills first
#     return (matched_skills * 1000) + (level_adequacy * 100)
#
# def filter_users_for_task(task, users):
#     """Return top 5 users with most relevant skills"""
#     print("\n=== DEBUG: Task Assignment ===")
#     print(f"Task {task.task_id} requires: {task.required_skills}\n")
#
#     candidates = []
#     for user in users:
#         score = skill_match_score(user.skills, task.required_skills)
#         print(f"User {user.user_id} skills: {user.skills}")
#         print(f"Score: {score}\n")
#         if score > 0:
#             heapq.heappush(candidates, (-score, user.user_id, user))
#
#     # Get top 5
#     top5 = [ (user, -score) for score, _, user in heapq.nsmallest(5, candidates) ]
#
#     print("=== Top 5 Candidates ===")
#     for idx, (user, score) in enumerate(top5, 1):
#         print(f"{idx}. {user.user_id} - Score: {score}")
#     print("========================")
#
#     return top5
#
# class TaskAssignmentCrew:
#     def __init__(self):
#         self.llm = LLM(
#             model="ollama/mistral",
#             base_url="http://localhost:11434",
#             api_key="",
#             temperature=0.3
#         )
#
#         @tool("SkillMatcher")
#         def skill_matcher(task_id: str) -> str:
#             """Returns top 3 qualified users in JSON format"""
#             task = SampleUserTask.objects(task_id=task_id).first()
#             if not task:
#                 return json.dumps({"error": "Task not found"})
#
#             matches = filter_users_for_task(task, SampleUser.objects())
#             return json.dumps({
#                 "valid_user_ids": [user.user_id for user, _ in matches],
#                 "matches": [
#                     {
#                         "user_id": user.user_id,
#                         "score": score,
#                         "matched_skills": list(user.skills.keys() & task.required_skills.keys())
#                     } for user, score in matches
#                 ]
#             })
#
#         self.manager = Agent(
#             role="Task Manager",
#             goal="Select FIRST user from valid_user_ids list",
#             backstory=(
#                 "Expert in technical task assignment. You MUST:\n"
#                 "1. Use ONLY the first user_id from valid_user_ids\n"
#                 "2. Never invent or modify IDs\n"
#                 "3. Ignore non-listed users\n"
#                 "4. Format output as {'user_id': 'UXXXX'}"
#             ),
#             tools=[skill_matcher],
#             llm=self.llm,
#             verbose=True,
#             max_iterations=3,
#             memory=True
#         )
#
#     def assign_task(self, task_id: str) -> str:
#         """Execute full assignment workflow with validation"""
#         try:
#             task = SampleUserTask.objects(task_id=task_id).first()
#             if not task:
#                 raise ValueError(f"Task {task_id} not found")
#
#             assignment_task = Task(
#                 description=f"Assign {task.name} ({task_id})",
#                 expected_output="{'user_id': 'UXXXX'} from valid_user_ids",
#                 agent=self.manager,
#                 output_json=AssignmentOutput
#             )
#
#             crew = Crew(
#                 agents=[self.manager],
#                 tasks=[assignment_task],
#                 process=Process.sequential,
#                 verbose=True
#             )
#             result = crew.kickoff()
#
#             best_user_id = self._parse_crew_response(result.raw)
#             logging.info(f"Selected user: {best_user_id}")
#
#             if not SampleUser.objects(user_id=best_user_id):
#                 raise ValueError(f"User {best_user_id} not in database")
#
#             return update_task_assignment(
#                 task_id=task_id,
#                 new_user_id=best_user_id,
#                 status='in_progress'
#             )
#
#         except Exception as e:
#             logging.error(f"Assignment failed: {str(e)}")
#             return f"Error: {str(e)}"
#
#     def _parse_crew_response(self, response: str) -> str:
#         """Strictly extract first valid user ID"""
#         try:
#             data = json.loads(response)
#             if "valid_user_ids" not in data or not data["valid_user_ids"]:
#                 raise ValueError("No valid users from SkillMatcher")
#             return data["valid_user_ids"][0]
#
#         except json.JSONDecodeError:
#             if match := re.search(r'\bU\d{4}\b', response):
#                 return match.group(0)
#             raise ValueError("No valid user ID found")
# app/agents/crewai_integration.py
# app/agents/crewai_integration.py
import json
import logging
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crewai import LLM
from app.models.sample_data import SampleUser, SampleUserTask
from app.agents.rag_agent import index_task_history, retrieve_similar_tasks
from app.utils.task_utils import update_task_assignment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define tools as standalone functions with proper decorators
@tool
def rag_tool(task_description: str) -> str:
    """Retrieve similar historical tasks based on task description"""
    try:
        if isinstance(task_description, dict):
            description = task_description.get('description', '')
        else:
            description = task_description
        logger.info(f"RAG tool searching for: {task_description}")

        # Find the task by name or task_id
        task = SampleUserTask.objects(name=description).first()
        if not task:
            # Try by task_id if name search fails
            task = SampleUserTask.objects(task_id=description).first()

        if not task:
            logger.warning(f"No task found matching: {task_description}")
            return json.dumps({
                "similar_tasks": [],
                "message": f"No task found matching '{task_description}'"
            })

        # Get similar tasks from RAG system
        similar_task_data = retrieve_similar_tasks(task, top_k=3)

        # Format the response properly
        formatted_results = []
        for similar in similar_task_data:
            try:
                formatted_results.append({
                    "task_id": similar.get("task_id", "unknown"),
                    "user_id": similar.get("user_id", "unknown"),
                    "similarity_score": similar.get("score", 0.0),
                    "document_preview": similar.get("document", "")[:200]
                })
            except Exception as e:
                logger.error(f"Error formatting similar task: {e}")
                continue

        result = {
            "query_task": {
                "task_id": task.task_id,
                "name": task.name,
                "required_skills": task.required_skills
            },
            "similar_tasks": formatted_results,
            "total_found": len(formatted_results)
        }

        logger.info(f"RAG tool found {len(formatted_results)} similar tasks")
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"RAG tool error: {str(e)}", exc_info=True)
        return json.dumps({
            "error": f"RAG tool failed: {str(e)}",
            "similar_tasks": []
        })

@tool
def user_db_tool(query: str) -> str:
    """Get user information - accepts user_id or 'all_available' to list available users"""
    try:
        logger.info(f"User DB tool query: {query}")

        if query.lower() == "all_available":
            # Return all available users
            available_users = SampleUser.objects(__raw__={
                'availability_status': 'available',
                '$expr': {'$lt': ['$current_ongoing_tasks', '$max_concurrent_tasks']}
            })

            users_data = []
            for user in available_users:
                users_data.append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "availability": user.availability_status,
                    "workload": f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}",
                    "skills": user.skills,
                    "experience": user.experience_level
                })

            return json.dumps({
                "available_users": users_data,
                "total_count": len(users_data)
            }, indent=2)

        else:
            # Get specific user
            user = SampleUser.objects(user_id=query).first()
            if not user:
                return json.dumps({
                    "error": f"User {query} not found",
                    "user_data": None
                })

            user_data = {
                "user_id": user.user_id,
                "username": user.username,
                "availability": user.availability_status,
                "workload": f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}",
                "skills": user.skills,
                "experience": user.experience_level,
                "can_take_more_tasks": user.current_ongoing_tasks < user.max_concurrent_tasks
            }

            return json.dumps({"user_data": user_data}, indent=2)

    except Exception as e:
        logger.error(f"User DB tool error: {str(e)}", exc_info=True)
        return json.dumps({
            "error": f"User DB tool failed: {str(e)}",
            "user_data": None
        })

@tool
def task_assignment_tool(task_id: str, user_id: str) -> str:
    """Assign a task to a user."""
    try:
        result = update_task_assignment(
            task_id=task_id,
            new_user_id=user_id,
            status='in_progress'
        )

        return json.dumps({
            "success": True,
            "assignment_result": result,
            "task_id": task_id,
            "assigned_to": user_id
        })

    except Exception as e:
        return json.dumps({"error": f"Assignment failed: {str(e)}"})

# def task_assignment_tool(assignment_data: str) -> str:
#     """Assign a task to a user. Input should be JSON with task_id and user_id"""
#     try:
#         logger.info(f"Task assignment tool input: {assignment_data}")
#
#         # Parse the assignment data
#         data = json.loads(assignment_data)
#         task_id = data.get("task_id")
#         user_id = data.get("user_id")
#
#         if not task_id or not user_id:
#             return json.dumps({
#                 "success": False,
#                 "error": "Both task_id and user_id are required"
#             })
#
#         # Verify task exists
#         task = SampleUserTask.objects(task_id=task_id).first()
#         if not task:
#             return json.dumps({
#                 "success": False,
#                 "error": f"Task {task_id} not found"
#             })
#
#         # Verify user exists and is available
#         user = SampleUser.objects(user_id=user_id).first()
#         if not user:
#             return json.dumps({
#                 "success": False,
#                 "error": f"User {user_id} not found"
#             })
#
#         if user.availability_status != 'available':
#             return json.dumps({
#                 "success": False,
#                 "error": f"User {user_id} is not available (status: {user.availability_status})"
#             })
#
#         if user.current_ongoing_tasks >= user.max_concurrent_tasks:
#             return json.dumps({
#                 "success": False,
#                 "error": f"User {user_id} is at capacity ({user.current_ongoing_tasks}/{user.max_concurrent_tasks})"
#             })
#
#         # Perform the assignment
#         result = update_task_assignment(
#             task_id=task_id,
#             new_user_id=user_id,
#             status='in_progress'
#         )
#
#         return json.dumps({
#             "success": True,
#             "assignment_result": result,
#             "task_id": task_id,
#             "assigned_to": user_id
#         })
#
#     except json.JSONDecodeError as e:
#         return json.dumps({
#             "success": False,
#             "error": f"Invalid JSON input: {str(e)}"
#         })
#     except Exception as e:
#         logger.error(f"Task assignment tool error: {str(e)}", exc_info=True)
#         return json.dumps({
#             "success": False,
#             "error": f"Assignment failed: {str(e)}"
#         })
import os

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
class TaskCrew:
    def __init__(self):
        self.llm = self._configure_llm()
        self.agents = self._create_agents()
        # Initialize RAG system
        try:
            index_task_history()
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")

    def _configure_llm(self):
        """Configure LLM with better error handling"""
        try:
            return LLM(
                model="gemini/gemini-1.5-flash",
                api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.3  # Increase from 0.1

            )
        except Exception as e:
            logger.error(f"LLM configuration failed: {e}")
            # Fallback to a simpler configuration
            return LLM(model="ollama/gemma:2b")

    def _create_agents(self):
        """Create agents with improved prompting"""
        return {
            'research': Agent(
                role='Task Researcher',
                goal='Find and analyze similar historical tasks to understand success patterns',
                backstory="""You are an expert task analyst who specializes in finding patterns 
                in historical task data. Your job is to search for similar completed tasks and 
                identify which users were successful with similar work.""",
                tools=[rag_tool],
                verbose=False,  # Change to False
                llm=self.llm,
                allow_delegation=False,
                max_execution_time=60,  # Increase timeout
                max_iter=3,  # Limit iterations
                step_callback=None
            ),
            'validation': Agent(
                role='Workload Validator',
                goal='Find available users who match the required skills and have capacity',
                backstory="""You are a meticulous resource manager who ensures optimal 
                workload distribution. You check user availability, current workload, 
                and skill compatibility before making recommendations.""",
                tools=[user_db_tool],
                verbose=False,  # Change to False
                llm=self.llm,
                allow_delegation=False,
                max_execution_time=60,  # Increase timeout
                max_iter=3,  # Limit iterations
                step_callback=None
            ),
            'assignment': Agent(
                role='Senior Task Manager',
                goal='Make the final task assignment decision based on research and validation',
                backstory="""You are an experienced project manager who makes final assignment 
                decisions. You consider historical success patterns, current workloads, and 
                skill matches to assign tasks to the most suitable team members.""",
                tools=[task_assignment_tool],
                verbose=False,  # Change to False
                llm=self.llm,
                allow_delegation=False,
                max_execution_time=60,  # Increase timeout
                max_iter=3,  # Limit iterations
                step_callback=None
            )
        }

    def assign_task(self, task_id: str) -> str:
        """Assign a task using the crew with improved error handling"""
        try:
            # Verify task exists
            task = SampleUserTask.objects(task_id=task_id).first()
            if not task:
                return f"Error: Task {task_id} not found"

            logger.info(f"Starting task assignment for: {task_id} - {task.name}")

            # Create tasks with more specific instructions
            research_task = Task(
                description=f"""Research similar tasks to "{task.name}" (ID: {task_id}).
                
                Required skills: {json.dumps(task.required_skills)}
                
                Use the rag_tool to find historical tasks and return a summary of:
                1. Similar tasks found
                2. Which users were successful with similar tasks
                3. Key patterns for success
                
                Return your findings in a clear, structured format.""",
                agent=self.agents['research'],
                expected_output="Detailed analysis of similar historical tasks and success patterns",
            )

            validation_task = Task(
                description=f"""Based on the research findings, validate which users are available 
                and suitable for the task "{task.name}".
                
                Required skills: {json.dumps(task.required_skills)}
                
                Use user_db_tool to:
                1. Get list of all available users
                2. Check their current workloads
                3. Verify skill compatibility
                
                Provide a ranked list of the top 3 candidates with reasoning.""",
                agent=self.agents['validation'],
                expected_output="Ranked list of top 3 available and qualified candidates",
                context=[research_task]
            )

            assignment_task = Task(
                description=f"""Assign {task.name} to best candidate.
    Use task_assignment_tool with JSON string format:
    '{{"task_id": {task_id}, "user_id": "selected_user_id"}}'
    """,
                agent=self.agents['assignment'],
                expected_output="Assignment confirmation with user ID",
                tools=[task_assignment_tool],
                verbose=True
            )

            # Create and run the crew
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=[research_task, validation_task, assignment_task],
                process=Process.sequential,
                verbose=True,
                max_execution_time=120  # 2 minute timeout
            )

            logger.info("Starting crew execution...")
            result = crew.kickoff()

            if result is None or str(result).strip() == "":
                logger.error("Crew returned empty result")
                return "Error: Assignment process completed but returned no result"

            logger.info(f"Crew execution completed successfully")
            return str(result)

        except Exception as e:
            logger.error(f"Task assignment failed: {str(e)}", exc_info=True)
            return f"Error: Task assignment failed - {str(e)}"

    def get_task_status(self, task_id: str) -> dict:
        """Get current status of a task"""
        try:
            task = SampleUserTask.objects(task_id=task_id).first()
            if not task:
                return {"error": f"Task {task_id} not found"}

            user_info = {}
            if task.user_id:
                user = SampleUser.objects(user_id=task.user_id).first()
                if user:
                    user_info = {
                        "user_id": user.user_id,
                        "username": user.username,
                        "current_workload": f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}"
                    }

            return {
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status,
                "assigned_to": user_info,
                "required_skills": task.required_skills,
                "due_date": task.due_date.isoformat() if task.due_date else None
            }

        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return {"error": f"Failed to get task status: {str(e)}"}

    def _validate_llm_response(self, response):
        """Validate LLM response is not empty"""
        if response is None or str(response).strip() == "":
            logger.error("Empty LLM response detected")
            return False
        return True
    def test_llm_connection(self):
        """Test LLM connection"""
        try:
            test_response = self.llm.invoke("Say 'test successful'")
            return test_response is not None and str(test_response).strip() != ""
        except Exception as e:
            logger.error(f"LLM test failed: {e}")
            return False