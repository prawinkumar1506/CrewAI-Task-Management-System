# Mistral Task Management System

A Python-based task management system that uses Mistral LLM for intelligent task assignment and reassignment.

## Features

- **Intelligent Task Assignment**: Uses Mistral LLM to assign tasks based on user skills, workload, and experience
- **RAG Integration**: ChromaDB for retrieving similar historical tasks to improve assignment decisions
- **MongoDB Integration**: Stores users, tasks, and assignment history
- **CLI Interface**: Interactive command-line chatbot for task management
- **Supervisor Agent**: Automated monitoring and reassignment of overdue tasks

## Setup

1. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Download Mistral model and place it in `./models/` directory

3. Update MongoDB connection string in `config.py`

4. Run the application:
\`\`\`bash
python run.py
\`\`\`

## Usage

The CLI chatbot provides options to:
- Assign tasks to users
- Reassign existing tasks
- Run supervisor checks
- List users and tasks
- View task assignment history

## Architecture

- **Models**: MongoDB documents for users and tasks
- **Agents**: Task assignment, reassignment, and supervision logic
- **Utils**: Data structure algorithms for efficient user filtering
- **RAG**: ChromaDB integration for historical task retrieval
- **LLM**: Mistral integration for intelligent decision making
#   C r e w A I - T a s k - M a n a g e m e n t - S y s t e m  
 