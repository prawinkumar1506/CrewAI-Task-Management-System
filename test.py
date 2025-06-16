'''import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def test_dialogpt():
    """Test if we can load and use DialoGPT model"""

    print("=== Testing DialoGPT Model ===")

    # Check if model files exist
    model_dir = "./models/test"
    print(f"Looking for model files in: {os.path.abspath(model_dir)}")

    if os.path.exists(model_dir):
        files = os.listdir(model_dir)
        print(f"Files found: {files}")
    else:
        print("Model directory not found!")
        return False

    try:
        print("\n1. Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
        print("✅ Tokenizer loaded successfully")

        print("\n2. Loading model...")
        model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")
        print("✅ Model loaded successfully")

        print("\n3. Testing generation...")
        # Test a simple conversation
        input_text = "Hello, how are you?"

        # Encode input
        input_ids = tokenizer.encode(input_text + tokenizer.eos_token, return_tensors='pt')

        # Generate response
        with torch.no_grad():
            output = model.generate(
                input_ids,
                max_length=input_ids.shape[1] + 50,
                num_beams=2,
                no_repeat_ngram_size=2,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode response
        response = tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True)

        print(f"Input: {input_text}")
        print(f"Response: {response}")
        print("✅ Model generation test successful!")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def create_simple_llm_function():
    """Create a simple LLM function using DialoGPT"""

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        # Load model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
        model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

        def query_dialogpt_llm(prompt, max_tokens=50):
            """Simple LLM query function using DialoGPT"""
            try:
                # Encode input
                input_ids = tokenizer.encode(prompt + tokenizer.eos_token, return_tensors='pt')

                # Generate response
                with torch.no_grad():
                    output = model.generate(
                        input_ids,
                        max_length=input_ids.shape[1] + max_tokens,
                        num_beams=2,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )

                # Decode response
                response = tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True)
                return response.strip()

            except Exception as e:
                return f"Error: {str(e)}"

        return query_dialogpt_llm

    except Exception as e:
        print(f"Failed to create LLM function: {e}")
        return None

if __name__ == "__main__":
    # Test the model
    success = test_dialogpt()

    if success:
        print("\n" + "="*50)
        print("DialoGPT is working! You can use this as a temporary replacement.")
        print("="*50)

        # Create the LLM function
        llm_func = create_simple_llm_function()
        if llm_func:
            print("\nTesting the LLM function...")
            test_response = llm_func("What is Python programming?", max_tokens=30)
            print(f"Test response: {test_response}")
    else:
        print("\n" + "="*50)
        print("DialoGPT test failed. Let's try a different approach.")
        print("="*50)'''

#from app.agents.mistral_llm import DialoGPTWrapper
#print(DialoGPTWrapper().call("Test prompt"))
# Generate task_history.json data
# app/models/insert_sample_data.py

import json
from datetime import datetime, timedelta
import random

# User skill profiles based on your data
user_skills = {
    'U0001': {'javascript': 9, 'react': 8, 'typescript': 7},
    'U0002': {'python': 9, 'nodejs': 8, 'mongodb': 7},
    'U0003': {'docker': 9, 'kubernetes': 8, 'aws': 7},
    'U0004': {'python': 8, 'machine_learning': 9, 'pytorch': 7},
    'U0005': {'swift': 8, 'kotlin': 7, 'flutter': 6},
    'U0006': {'selenium': 8, 'cypress': 7, 'postman': 6},
    'U0007': {'javascript': 9, 'react': 8, 'typescript': 7, 'python': 9, 'nodejs': 8, 'mongodb': 7},
    'U0008': {'docker': 9, 'kubernetes': 8, 'aws': 7},
    'U0009': {'python': 9, 'nodejs': 8, 'mongodb': 7},
    'U0010': {'python': 8, 'machine_learning': 9, 'pytorch': 7},
    'U0011': {'swift': 8, 'kotlin': 7, 'flutter': 6},
    'U0012': {'selenium': 8, 'cypress': 7, 'postman': 6},
    'U0013': {'javascript': 9, 'react': 8, 'typescript': 7},
    'U0014': {'docker': 9, 'kubernetes': 8, 'aws': 7},
    'U0015': {'python': 8, 'machine_learning': 9, 'pytorch': 7},
    'U0016': {'swift': 8, 'kotlin': 7, 'flutter': 6},
    'U0017': {'python': 9, 'nodejs': 8, 'mongodb': 7},
    'U0018': {'javascript': 9, 'react': 8, 'typescript': 7},
    'U0019': {'selenium': 8, 'cypress': 7, 'postman': 6},
    'U0020': {'python': 9, 'nodejs': 8, 'mongodb': 7, 'docker': 9, 'kubernetes': 8, 'aws': 7}
}

# Domain-specific task templates
task_templates = {
    'frontend': [
        ("React Component Migration", ["react", "javascript"], 2),
        ("TypeScript Conversion", ["typescript", "javascript"], 3),
        ("Performance Optimization", ["react", "javascript"], 2)
    ],
    'backend': [
        ("API Gateway Implementation", ["python", "nodejs"], 2),
        ("Database Sharding", ["mongodb", "python"], 3),
        ("Microservices Refactor", ["nodejs", "docker"], 3)
    ],
    'devops': [
        ("K8s Cluster Setup", ["kubernetes", "docker"], 3),
        ("Cloud Migration", ["aws", "docker"], 2),
        ("CI/CD Pipeline", ["docker", "aws"], 2)
    ],
    'data': [
        ("ML Model Training", ["python", "machine_learning"], 3),
        ("Data Pipeline", ["python", "pytorch"], 2),
        ("Feature Engineering", ["machine_learning", "python"], 2)
    ],
    'mobile': [
        ("iOS Offline Mode", ["swift", "kotlin"], 2),
        ("Android Memory Optimization", ["kotlin", "flutter"], 3),
        ("Cross-platform UI", ["flutter", "swift"], 2)
    ],
    'qa': [
        ("E2E Test Suite", ["selenium", "postman"], 3),
        ("Load Testing Framework", ["cypress", "postman"], 3),
        ("Security Audit", ["selenium", "cypress"], 2)
    ]
}

def find_qualified_users(required_skills):
    qualified = []
    for user_id, skills in user_skills.items():
        if all(skill in skills for skill in required_skills):
            qualified.append(user_id)
    return qualified

def generate_realistic_history():
    history = []
    task_id = 22  # Starting from T0022

    for domain, templates in task_templates.items():
        for template in templates:
            name, skills, count = template
            for _ in range(count):
                qualified_users = find_qualified_users(skills)
                if not qualified_users:
                    continue  # Skip if no qualified users

                user_id = random.choice(qualified_users)
                task_data = {
                    "task_id": f"T{task_id:04d}",
                    "user_id": user_id,
                    "name": f"{name} ({domain})",
                    "required_skills": {s: user_skills[user_id][s] for s in skills},
                    "completed_at": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
                    "outcome": random.choices(["success", "partial_success"], [0.85, 0.15])[0],
                    "complexity": random.choices(["low", "medium", "high"], [0.2, 0.5, 0.3])[0]
                }
                history.append(task_data)
                task_id += 1

    # Ensure we have at least 20 tasks
    while len(history) < 500:
        domain = random.choice(list(task_templates.keys()))
        template = random.choice(task_templates[domain])
        name, skills, _ = template
        qualified_users = find_qualified_users(skills)
        if qualified_users:
            user_id = random.choice(qualified_users)
            task_data = {
                "task_id": f"T{task_id:04d}",
                "user_id": user_id,
                "name": f"{name} ({domain})",
                "required_skills": {s: user_skills[user_id][s] for s in skills},
                "completed_at": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
                "outcome": random.choices(["success", "partial_success"], [0.85, 0.15])[0],
                "complexity": random.choices(["low", "medium", "high"], [0.2, 0.5, 0.3])[0]
            }
            history.append(task_data)
            task_id += 1

    with open("app/data/task_history.json", "w") as f:
        json.dump(history, f, indent=2)

generate_realistic_history()
