# app/test.py
from app.models.sample_data import SampleUserTask
from app.agents.crewai_integration import TaskCrew

def test_assignment():
    # Create sample task
    # task = SampleUserTask(
    #     task_id="T1008",
    #     name="Mobile Auth",
    #     required_skills={"python": 8, "security": 7},
    #     status="pending"
    # )
    # task.save()

    # Test assignment
    # Test RAG system first
    from app.agents.rag_agent import index_task_history, get_rag_stats
    index_task_history()
    print(get_rag_stats())

    # Test the crew
    from app.agents.crewai_integration import TaskCrew
    crew = TaskCrew()
    crew.test_llm_connection()
    result = crew.assign_task("T0004")
    crew._validate_llm_response(result)

    print(result)

if __name__ == "__main__":
    test_assignment()
