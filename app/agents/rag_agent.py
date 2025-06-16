# # app/agents/rag_agent.py
#
# import chromadb
# from app.models.sample_data import SampleUser,SampleUserTask
#
# import json
# import os
#
# # Initialize ChromaDB PersistentClient (v0.4+ API)
# # Replace existing Chroma client initialization
# '''chroma_client = chromadb.PersistentClient(
#     path="./chroma_db",
#     settings=Settings(
#         chroma_db_impl="duckdb+parquet",
#         allow_reset=True
#     )
# )'''
# chroma_client = chromadb.PersistentClient(
#     path="./chroma_db"
# )
#
# # Add explicit collection creation
# collection = chroma_client.get_or_create_collection(
#     name="task_history",
#     metadata={"hnsw:space": "cosine"}
# )
#
#
# # Create or load the task history collection
# collection_name = "task_history"
# collection = chroma_client.get_or_create_collection(name=collection_name)
#
# def index_task_history():
#     """Index historical tasks from MongoDB into Chroma."""
#     try:
#         tasks = SampleUserTask.objects(status='completed')
#         documents = []
#         metadatas = []
#         ids = []
#
#         for task in tasks:
#             doc = f"Task: {task.name}\nSkills: {json.dumps(task.required_skills)}\nLog: {json.dumps(task.assignment_log)}"
#             documents.append(doc)
#             metadatas.append({
#                 "task_id": task.task_id,
#                 "user_id": task.user_id
#             })
#             ids.append(task.task_id)
#
#         # Add to Chroma collection
#         if documents:
#             collection.add(
#                 documents=documents,
#                 metadatas=metadatas,
#                 ids=ids
#             )
#         with open("app/data/task_history.json", "w") as f:
#             for task in tasks:
#                 history.append({
#                     "task_id": task.task_id,
#                     "name": task.name,
#                     "user_id": task.user_id,
#                     "skills": task.required_skills,
#                     "outcome": "success" if task.status == 'completed' else "failed"
#                 })
#             json.dump(history, f)
#     except Exception as e:
#         print(f"Indexing failed: {str(e)}")
#
# def retrieve_similar_tasks(task, top_k=3):
#     """Retrieve similar tasks from history based on task name and required skills."""
#     query_text = f"Task: {task.name}\nSkills: {json.dumps(task.required_skills)}"
#
#     results = collection.query(
#         query_texts=[query_text],
#         n_results=top_k
#     )
#
#     similar_tasks = []
#     for i in range(top_k):
#         if i < len(results["ids"][0]):
#             task_id = results["ids"][0][i]
#             metadata = results["metadatas"][0][i]
#             document = results["documents"][0][i]
#             similar_tasks.append({
#                 "task_id": task_id,
#                 "user_id": metadata.get("user_id"),
#                 "document": document
#             })
#
#     return similar_tasks
# app/agents/rag_agent.py
# app/agents/rag_agent.py
















#version 2 gaali
# import chromadb
#
# from chromadb.utils import embedding_functions
# from app.models.sample_data import SampleUserTask
# import json
#
# class RAGSystem:
#     _instance = None
#
#     def __new__(cls):
#         if not cls._instance:
#             cls._instance = super().__new__(cls)
#             cls._instance.client = chromadb.PersistentClient(path="./chroma_db")
#             cls._instance.embedder = embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
#             cls._instance.collection = cls._instance.client.get_or_create_collection(
#                 name="task_history",
#                 embedding_function=cls._instance.embedder,
#                 metadata={"hnsw:space": "cosine"}
#             )
#         return cls._instance
#
#     def index_completed_tasks(self):
#         """Index all completed tasks daily"""
#         tasks = SampleUserTask.objects(status='completed')
#         documents, metadatas, ids = [], [], []
#
#         for task in tasks:
#             doc = self._create_task_document(task)
#             documents.append(doc)
#             metadatas.append(self._create_task_metadata(task))
#             ids.append(task.task_id)
#
#         if documents:
#             self.collection.upsert(
#                 documents=documents,
#                 metadatas=metadatas,
#                 ids=ids
#             )
#             self._update_task_history_file(tasks)
#
#     def _create_task_document(self, task) -> str:
#         return f"""
#         Task: {task.name}
#         Type: {task.task_type}
#         Skills: {json.dumps(task.required_skills)}
#         Outcome: {'Success' if task.status == 'completed' else 'Failed'}
#         Duration: {(task.due_date - task.started_at).days if task.started_at else 0} days
#         """
#
#     def _create_task_metadata(self, task) -> dict:
#         return {
#             "task_id": task.task_id,
#             "user_id": task.user_id,
#             "complexity": task.priority,
#             "completion_date": task.due_date.isoformat()
#         }
#
#     def _update_task_history_file(self, tasks):
#         history = [self._create_task_metadata(t) for t in tasks]
#         with open("app/data/task_history.json", "w") as f:
#             json.dump(history, f, indent=2)
#
#     def retrieve_similar_tasks(self, task, top_k: int = 3) -> list:
#         query_text = f"Task: {task.name}\nSkills: {json.dumps(task.required_skills)}"
#         results = self.collection.query(
#             query_texts=[query_text],
#             n_results=top_k,
#             include=["documents", "metadatas"]
#         )
#         return [{
#             "task_id": meta['task_id'],
#             "user_id": meta['user_id'],
#             "document": doc,
#             "complexity": meta['complexity']
#         } for doc, meta in zip(results['documents'][0], results['metadatas'][0])]
#
# # Singleton instance
# rag_system = RAGSystem()
#
# # Module-level exports
# def index_task_history():
#     rag_system.index_completed_tasks()
#
# def retrieve_similar_tasks(task, top_k=3):
#     return rag_system.retrieve_similar_tasks(task, top_k)

# app/agents/rag_agent.py
import chromadb
from chromadb.utils import embedding_functions
from app.models.sample_data import SampleUserTask
import json
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path="./chroma_db")
            self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

            # Unique collection name based on embedding model
            self.model_hash = hashlib.md5("all-MiniLM-L6-v2".encode()).hexdigest()[:8]
            self.collection_name = f"task_history_{self.model_hash}"

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedder,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"RAG system initialized with collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise

    def index_completed_tasks(self):
        """Index completed tasks with robust error handling"""
        try:
            # Get all completed tasks
            completed_tasks = list(SampleUserTask.objects(status='completed'))

            if not completed_tasks:
                logger.warning("No completed tasks found to index")
                return

            documents, metadatas, ids = [], [], []

            for task in completed_tasks:
                try:
                    # Create document text
                    skills_text = ", ".join([f"{skill}:{level}" for skill, level in task.required_skills.items()])
                    doc_text = f"Task: {task.name}\nSkills Required: {skills_text}\nType: {task.task_type or 'feature'}\nPriority: {task.priority}"

                    # Calculate duration if possible
                    duration_days = 0
                    if task.started_at and task.completed_at:
                        duration_days = (task.completed_at - task.started_at).days
                    elif task.created_at and task.completed_at:
                        duration_days = (task.completed_at - task.created_at).days

                    # Create metadata
                    metadata = {
                        "task_id": str(task.task_id),
                        "user_id": str(task.user_id) if task.user_id else "unknown",
                        "priority": str(task.priority),
                        "task_type": str(task.task_type) if task.task_type else "feature",
                        "duration_days": int(duration_days),
                        "effort_hours": float(task.actual_effort_hours) if task.actual_effort_hours else 0.0,
                        "skills_count": len(task.required_skills),
                        "completed_date": task.completed_at.isoformat() if task.completed_at else datetime.utcnow().isoformat()
                    }

                    documents.append(doc_text)
                    metadatas.append(metadata)
                    ids.append(str(task.task_id))

                except Exception as e:
                    logger.warning(f"Failed to process task {task.task_id}: {e}")
                    continue

            if documents:
                # Upsert to collection
                self.collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Successfully indexed {len(documents)} completed tasks")
            else:
                logger.warning("No valid documents to index")

        except Exception as e:
            logger.error(f"Task indexing failed: {str(e)}", exc_info=True)
            raise

    def retrieve_similar_tasks(self, task, top_k=3):
        """Retrieve similar tasks with improved error handling"""
        try:
            if not task:
                logger.error("No task provided for similarity search")
                return []

            # Validate task object
            if not hasattr(task, 'name') or not hasattr(task, 'required_skills'):
                logger.error("Invalid task object - missing required attributes")
                return []

            if not task.name or not task.required_skills:
                logger.error("Task name or required_skills is empty")
                return []

            # Create query text
            skills_text = ", ".join([f"{skill}:{level}" for skill, level in task.required_skills.items()])
            query_text = f"Task: {task.name}\nSkills Required: {skills_text}\nType: {task.task_type or 'feature'}\nPriority: {task.priority}"

            logger.info(f"Searching for similar tasks with query: {query_text[:100]}...")

            # Query the collection
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(top_k, 10),  # Limit to reasonable number
                include=["documents", "metadatas", "distances"]
            )

            # Validate results structure
            if not results or not isinstance(results, dict):
                logger.warning("Empty or invalid results from ChromaDB")
                return []

            # Safely extract results
            documents = results.get("documents", [[]])[0] if results.get("documents") else []
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            distances = results.get("distances", [[]])[0] if results.get("distances") else []

            if not documents:
                logger.info("No similar tasks found")
                return []

            # Process results
            similar_tasks = []
            for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances)):
                try:
                    # Skip if this is the same task
                    if meta.get("task_id") == task.task_id:
                        continue

                    similarity_score = round(1 - distance, 3) if distance is not None else 0.0

                    similar_task = {
                        "task_id": meta.get("task_id", "unknown"),
                        "user_id": meta.get("user_id", "unknown"),
                        "score": similarity_score,
                        "document": doc[:300] if doc else "",  # Truncate for readability
                        "metadata": {
                            "priority": meta.get("priority", "unknown"),
                            "task_type": meta.get("task_type", "unknown"),
                            "duration_days": meta.get("duration_days", 0),
                            "effort_hours": meta.get("effort_hours", 0.0),
                            "skills_count": meta.get("skills_count", 0)
                        }
                    }

                    similar_tasks.append(similar_task)

                except Exception as e:
                    logger.warning(f"Failed to process similarity result {i}: {e}")
                    continue

            # Sort by similarity score and return top results
            similar_tasks.sort(key=lambda x: x["score"], reverse=True)
            final_results = similar_tasks[:top_k]

            logger.info(f"Found {len(final_results)} similar tasks")
            return final_results

        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}", exc_info=True)
            return []

    def get_collection_stats(self):
        """Get statistics about the indexed collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "indexed_tasks": count,
                "status": "healthy" if count > 0 else "empty"
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "indexed_tasks": 0,
                "status": "error",
                "error": str(e)
            }

# Create singleton instance
try:
    rag_system = RAGSystem()
except Exception as e:
    logger.error(f"Failed to create RAG system: {e}")
    rag_system = None

# Public interface functions
def index_task_history():
    """Index completed tasks into RAG system"""
    if rag_system is None:
        logger.error("RAG system not initialized")
        return False

    try:
        rag_system.index_completed_tasks()
        return True
    except Exception as e:
        logger.error(f"Failed to index task history: {e}")
        return False

def retrieve_similar_tasks(task, top_k=3):
    """Retrieve similar tasks from RAG system"""
    if rag_system is None:
        logger.error("RAG system not initialized")
        return []

    try:
        return rag_system.retrieve_similar_tasks(task, top_k)
    except Exception as e:
        logger.error(f"Failed to retrieve similar tasks: {e}")
        return []

def get_rag_stats():
    """Get RAG system statistics"""
    if rag_system is None:
        return {"status": "not_initialized"}

    return rag_system.get_collection_stats()