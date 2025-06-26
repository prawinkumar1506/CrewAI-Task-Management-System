# 🤖 AI Task Management System with CrewAI & Gemini LLM

A powerful Python-based task management system that leverages **CrewAI**, **AI agent orchestration**, and **Gemini LLM** for intelligent task assignment, reassignment, and supervision.

---

## 🚀 Key Features

- 🔍 **Intelligent Task Assignment**  
  Uses **Gemini LLM** to assign tasks based on users' skills, availability, workload, and experience levels.

- 🧠 **Multi-Agent Orchestration with CrewAI**  
  Seamless coordination between **Task Assignment Agent**, **Task Reassignment Agent**, **Load Balancer**, and **Supervisor Agent** using [CrewAI](https://github.com/joaomdmoura/crewAI).

- 🗃️ **RAG Integration (ChromaDB)**  
  Integrates **ChromaDB** to retrieve semantically similar past tasks using **Retrieval-Augmented Generation** (RAG) to improve assignment decisions.

- 🛢️ **MS SQL Integration**  
  Stores and manages all user, task, and assignment data in a relational **Microsoft SQL Server** database. Live updates reflected dynamically.

- 🛠️ **Interactive CLI Chatbot**  
  A natural language chatbot for managing tasks, querying users, listing assignments, and interacting with the system using simple text input.

- 📈 **Automated Task Supervision**  
  A **Supervisor Agent** monitors overdue tasks and automatically reassigns them or alerts users, keeping the workflow healthy and balanced.

---

## 🧬 System Architecture

```
User <--> CLI Chatbot <--> Supervisor LLM (Gemini)
                           |
                           |
    -----------------------------------------------
    |                      |                     |
Task Assignment Agent   Reassignment Agent   Load Manager Agent
    |                      |                     |
[MS SQL DB]       <--> ChromaDB (RAG) <--> [LLM Decision Layer]
```

- **CrewAI**: Handles multi-agent orchestration  
- **LLM Decision Layer**: Powered by Gemini for reasoning and ranking  
- **ChromaDB**: Vector similarity for task context & retrieval  
- **MS SQL**: Centralized relational database for persistent data  
- **CLI Bot**: Chat interface to interact with the system  

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/CrewAI-Task-Management-System.git
cd CrewAI-Task-Management-System
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure MS SQL

Update your MS SQL connection string in `config.py`:

```python
SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://username:password@localhost/dbname?driver=ODBC+Driver+17+for+SQL+Server"
```

Ensure your MS SQL Server is running and the schema matches `db/schema.sql`.

### 4. Run the Application

```bash
python app\agents\llm_orchestrator.py
```

---

## 🛠️ CLI Usage Guide

Interact via natural language CLI:

```bash
> Assign a new task  
> Reassign task T123  
> List all users  
> Show all tasks  
> View task history  
> Run supervisor check  
```

---

## 🤖 AI Agents (via CrewAI)

| Agent                | Role                                                                 |
| -------------------- | -------------------------------------------------------------------- |
| 🧠 Task Assign Agent | Matches tasks with the best-suited user using LLM + skills filtering |
| 🔁 Reassign Agent    | Re-evaluates unassigned/overdue tasks and reallocates them           |
| ⚖️ Load Manager      | Balances task load to avoid overburdening individuals                |
| 🕵️ Supervisor Agent | Periodically scans for delays or misassignments                      |

Each agent is independently callable and interacts with the central LLM.

---

## 🧠 AI & RAG Capabilities

* **Gemini LLM**: Decision-making engine for matching, prioritization, and supervision
* **RAG with ChromaDB**:
  * Past tasks are embedded and stored in vector format
  * During assignment, the system retrieves similar historical tasks to guide LLM decisions

✅ Logs every decision made by the LLM in `logs/assignment_log.json`  
✅ Supports admin override in CLI for all AI decisions  
✅ Task versioning and rollback via MS SQL triggers (optional)

---

## 📚 Future Enhancements

* Web-based dashboard using React + Flask API
* JWT-based user authentication for secure access
* Integration with Slack/Teams for notification automation
* Graph-based scheduling visualization
* Agent-as-API mode for chatbot/voice UI integration

---

## 🙌 Contributions

Feel free to fork, enhance, or contribute to the project!

```bash
git clone https://github.com/your-username/CrewAI-Task-Management-System.git
```

> Made with ❤️ by AI and Human Orchestration
