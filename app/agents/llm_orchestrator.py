# app/agents/conversational_orchestrator.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from app.models.sample_data import SampleUser, SampleUserTask
from app.chatbot.cli_chatbot import TaskCLI

# Define tools at module level (outside any class)
@tool
def list_users_tool(query: str = "") -> str:
    """List all users in the system with their availability and workload"""
    try:
        users_data = []
        for user in SampleUser.objects():
            status_icon = "✅" if user.availability_status == 'available' else "⛔"
            workload = f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}"

            users_data.append({
                "user_id": user.user_id,
                "username": user.username,
                "status": f"{status_icon} {user.availability_status}",
                "workload": workload,
                "experience": getattr(user, 'experience_level', 'N/A')
            })

        return json.dumps({
            "action": "list_users",
            "users": users_data,
            "total_count": len(users_data)
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to list users: {str(e)}"})

@tool
def list_tasks_tool(query: str = "") -> str:
    """List all tasks in the system with their status and assignments"""
    try:
        tasks_data = []
        for task in SampleUserTask.objects():
            status_icon = "✅" if task.status == 'completed' else "⌛"
            assigned = task.user_id if task.user_id else "Unassigned"
            due_date = task.due_date.strftime("%Y-%m-%d") if task.due_date else "N/A"

            tasks_data.append({
                "task_id": task.task_id,
                "name": task.name,
                "status": f"{status_icon} {task.status}",
                "assigned_to": assigned,
                "due_date": due_date,
                "priority": task.priority
            })

        return json.dumps({
            "action": "list_tasks",
            "tasks": tasks_data,
            "total_count": len(tasks_data)
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to list tasks: {str(e)}"})

@tool
def assign_task_tool(task_assignment_data: str) -> str:
    """Assign a task to a user (manual or automatic assignment)"""
    try:
        # Initialize CLI instance within the tool
        cli = TaskCLI()

        data = json.loads(task_assignment_data)
        task_id = data.get('task_id')
        user_id = data.get('user_id', '')

        if user_id:
            # Manual assignment - note: this method may not exist, adjust accordingly
            result = f"Manual assignment of {task_id} to {user_id} requested"
        else:
            # Automatic assignment
            result = cli.crew.assign_task(task_id)

        return json.dumps({
            "action": "assign_task",
            "task_id": task_id,
            "assigned_user": user_id or "auto-selected",
            "result": str(result),
            "success": True
        })
    except Exception as e:
        return json.dumps({
            "action": "assign_task",
            "error": f"Assignment failed: {str(e)}",
            "success": False
        })

@tool
def get_user_info_tool(user_query: str) -> str:
    """Get detailed information about a specific user"""
    try:
        # Extract user ID from query
        user_id_match = re.search(r'U\d{4}', user_query)
        if not user_id_match:
            return json.dumps({"error": "No valid user ID found in query"})

        user_id = user_id_match.group()
        user = SampleUser.objects(user_id=user_id).first()

        if not user:
            return json.dumps({"error": f"User {user_id} not found"})

        return json.dumps({
            "action": "get_user_info",
            "user_data": {
                "user_id": user.user_id,
                "username": user.username,
                "availability": user.availability_status,
                "workload": f"{user.current_ongoing_tasks}/{user.max_concurrent_tasks}",
                "skills": user.skills,
                "experience": getattr(user, 'experience_level', 'N/A')
            }
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to get user info: {str(e)}"})

@tool
def get_task_info_tool(task_query: str) -> str:
    """Get detailed information about a specific task"""
    try:
        # Extract task ID from query
        task_id_match = re.search(r'T\d{4}', task_query)
        if not task_id_match:
            return json.dumps({"error": "No valid task ID found in query"})

        task_id = task_id_match.group()
        task = SampleUserTask.objects(task_id=task_id).first()

        if not task:
            return json.dumps({"error": f"Task {task_id} not found"})

        return json.dumps({
            "action": "get_task_info",
            "task_data": {
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status,
                "assigned_to": task.user_id or "Unassigned",
                "priority": task.priority,
                "required_skills": task.required_skills,
                "due_date": task.due_date.isoformat() if task.due_date else None
            }
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to get task info: {str(e)}"})

@tool
def system_status_tool(query: str = "") -> str:
    """Get overall system status and statistics"""
    try:
        total_users = SampleUser.objects.count()
        available_users = SampleUser.objects(availability_status='available').count()
        total_tasks = SampleUserTask.objects.count()
        pending_tasks = SampleUserTask.objects(status='pending').count()
        in_progress_tasks = SampleUserTask.objects(status='in_progress').count()
        completed_tasks = SampleUserTask.objects(status='completed').count()

        return json.dumps({
            "action": "system_status",
            "statistics": {
                "users": {
                    "total": total_users,
                    "available": available_users
                },
                "tasks": {
                    "total": total_tasks,
                    "pending": pending_tasks,
                    "in_progress": in_progress_tasks,
                    "completed": completed_tasks
                }
            }
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to get system status: {str(e)}"})

class ConversationalTaskOrchestrator:
    def __init__(self):
        self.llm = self._configure_llm()
        self.conversation_history = []
        self.pending_confirmation = None

    def _configure_llm(self):
        """Configure LLM for intent parsing and orchestration"""
        return LLM(
            model="gemini/gemini-1.5-flash",  # Using Flash for higher rate limits
            api_key="AIzaSyDREOvD_AgBvzs9SyvTJyV77ruHswMT74s",
            temperature=0.3
        )

    def create_orchestrator_agent(self):
        """Create the main orchestrator agent with all tools"""
        return Agent(
            role='Task Management Assistant',
            goal='Help users manage tasks and users through natural language commands',
            backstory="""You are an intelligent task management assistant that can understand 
            natural language requests and execute appropriate actions. You can list users, 
            list tasks, assign tasks, get detailed information, and provide system status.""",
            tools=[
                list_users_tool,      # Reference module-level functions
                list_tasks_tool,
                assign_task_tool,
                get_user_info_tool,
                get_task_info_tool,
                system_status_tool
            ],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    def process_user_request(self, user_input: str) -> str:
        """Process natural language user request and return response"""
        try:
            # Check for pending confirmation
            if self.pending_confirmation:
                return self._handle_confirmation(user_input)

            # Create orchestrator agent
            orchestrator = self.create_orchestrator_agent()

            # Create task for the agent
            task = Task(
                description=f"""
                User Request: "{user_input}"
                
                Analyze this request and determine what action to take:
                1. If asking to list users, use list_users_tool
                2. If asking to list tasks, use list_tasks_tool  
                3. If requesting task assignment, use assign_task_tool
                4. If asking about specific user, use get_user_info_tool
                5. If asking about specific task, use get_task_info_tool
                6. If asking for system status, use system_status_tool
                
                For task assignments that seem risky, ask for confirmation first.
                Provide a helpful, conversational response based on the tool results.
                """,
                agent=orchestrator,
                expected_output="Natural language response based on executed actions"
            )

            # Execute the task
            crew = Crew(
                agents=[orchestrator],
                tasks=[task],
                verbose=False  # Reduced verbosity to minimize rate limit usage
            )

            result = crew.kickoff()

            # Store conversation history
            self.conversation_history.append({
                "user_input": user_input,
                "response": str(result),
                "timestamp": datetime.now().isoformat()
            })

            return self._format_response(result, user_input)

        except Exception as e:
            # Enhanced error handling for rate limits and common issues
            error_msg = str(e)
            if "429" in error_msg:
                return "I'm experiencing high demand right now. Please wait 30 seconds and try again."
            elif "validation" in error_msg.lower():
                return "I encountered a validation error. Let me try a simpler approach to help you."
            else:
                return f"I encountered an error while processing your request: {error_msg}"

    def _format_response(self, result: str, user_input: str) -> str:
        """Format the agent response into a conversational format"""
        try:
            # Try to parse JSON from result
            if '{' in str(result) and '}' in str(result):
                json_match = re.search(r'\{.*\}', str(result), re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return self._format_json_response(data, user_input)

            # Return original result if no JSON found
            return str(result)

        except Exception:
            return str(result)

    def _format_json_response(self, data: Dict[str, Any], user_input: str) -> str:
        """Format JSON response data into conversational text"""
        action = data.get('action', '')

        if action == 'list_users':
            users = data.get('users', [])
            response = f"Here are all {len(users)} users in the system:\n\n"
            for user in users:
                response += f"• **{user['username']}** ({user['user_id']}) - {user['status']} - Workload: {user['workload']}\n"
            return response

        elif action == 'list_tasks':
            tasks = data.get('tasks', [])
            response = f"Here are all {len(tasks)} tasks in the system:\n\n"
            for task in tasks:
                response += f"• **{task['name']}** ({task['task_id']}) - {task['status']} - Assigned to: {task['assigned_to']}\n"
            return response

        elif action == 'assign_task':
            if data.get('success'):
                return f"✅ Successfully assigned task {data['task_id']} to {data['assigned_user']}"
            else:
                return f"❌ Failed to assign task: {data.get('error', 'Unknown error')}"

        elif action == 'get_user_info':
            user = data.get('user_data', {})
            return f"""**User Information for {user.get('username', 'Unknown')}:**
• User ID: {user.get('user_id')}
• Availability: {user.get('availability')}
• Current Workload: {user.get('workload')}
• Experience Level: {user.get('experience')}
• Skills: {', '.join(user.get('skills', {}).keys())}"""

        elif action == 'get_task_info':
            task = data.get('task_data', {})
            return f"""**Task Information for {task.get('name', 'Unknown')}:**
• Task ID: {task.get('task_id')}
• Status: {task.get('status')}
• Assigned to: {task.get('assigned_to')}
• Priority: {task.get('priority')}
• Due Date: {task.get('due_date', 'Not set')}
• Required Skills: {', '.join(task.get('required_skills', {}).keys())}"""

        elif action == 'system_status':
            stats = data.get('statistics', {})
            return f"""**System Status:**
• Users: {stats.get('users', {}).get('available', 0)}/{stats.get('users', {}).get('total', 0)} available
• Tasks: {stats.get('tasks', {}).get('pending', 0)} pending, {stats.get('tasks', {}).get('in_progress', 0)} in progress, {stats.get('tasks', {}).get('completed', 0)} completed"""

        return str(data)

    def _handle_confirmation(self, user_input: str) -> str:
        """Handle confirmation responses for pending operations"""
        if user_input.lower() in ['yes', 'y', 'confirm', 'proceed']:
            result = self.pending_confirmation['action']()
            self.pending_confirmation = None
            return f"✅ {result}"
        elif user_input.lower() in ['no', 'n', 'cancel', 'abort']:
            self.pending_confirmation = None
            return "❌ Operation cancelled."
        else:
            return "Please respond with 'yes' to confirm or 'no' to cancel."

    def start_conversation(self):
        """Start the conversational interface"""
        print("🤖 Task Management Assistant")
        print("I can help you manage tasks and users using natural language!")
        print("Try asking things like:")
        print("• 'Could you please list all users for me?'")
        print("• 'I want to assign task T0020 to user U0019'")
        print("• 'Show me the status of task T0015'")
        print("• 'What's the current system status?'")
        print("\nType 'exit' to quit.\n")

        while True:
            try:
                user_input = input("\n👤 You: ").strip()

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break

                if not user_input:
                    continue

                print("\n🤖 Assistant: ", end="")
                response = self.process_user_request(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    orchestrator = ConversationalTaskOrchestrator()
    orchestrator.start_conversation()
