# """
# Enhanced temporary LLM replacement with robust JSON handling
# """
# from app.models.sample_data import SampleUser,SampleUserTask
# from app.utils.dsa_utils import filter_users_for_task
#
# import os
# import re
# import json
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer
#
# # Global variables to store model and tokenizer
# model = None
# tokenizer = None
#
# def initialize_model():
#     """Initialize the DialoGPT model and tokenizer with proper settings"""
#     global model, tokenizer
#
#     if model is None or tokenizer is None:
#         print("Loading DialoGPT model...")
#         try:
#             tokenizer = AutoTokenizer.from_pretrained(
#                 "microsoft/DialoGPT-small",
#                 padding_side='left',
#                 pad_token='<|endoftext|>'
#             )
#             model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")
#             print("✅ DialoGPT model loaded successfully")
#         except Exception as e:
#             print(f"❌ Failed to load DialoGPT: {e}")
#             raise e
#
# def query_mistral_llm(prompt,task, max_tokens=200, max_retries=3):
#     initialize_model()
#
#     system_prompt = """You are a task assignment AI. Return ONLY valid JSON in this format:
# {
#   "user_id": "UXXXX",
#   "reason": "detailed explanation"
# }"""
#
#     full_prompt = f"{system_prompt}\n\n{prompt}\n\nResponse:"
#
#     for attempt in range(max_retries):
#         try:
#             inputs = tokenizer(
#                 full_prompt,
#                 return_tensors="pt",
#                 padding=True,
#                 truncation=True,
#                 max_length=512
#             )
#
#             output = model.generate(
#                 inputs.input_ids,
#                 attention_mask=inputs.attention_mask,
#                 max_new_tokens=max_tokens,
#                 num_beams=3,
#                 early_stopping=True,
#                 pad_token_id=tokenizer.eos_token_id
#             )
#
#             raw_response = tokenizer.decode(output[0], skip_special_tokens=True)
#
#             # Improved JSON extraction with stack balancing
#             def extract_first_json(text):
#                 start = text.find('{')
#                 if start == -1: return None
#                 stack = []
#                 result = []
#                 for char in text[start:]:
#                     result.append(char)
#                     if char == '{':
#                         stack.append(char)
#                     elif char == '}':
#                         if stack: stack.pop()
#                         if not stack: return ''.join(result)
#                 return None
#
#             json_str = extract_first_json(raw_response)
#
#             if json_str:
#                 parsed = json.loads(json_str)
#                 if SampleUser.objects(user_id=parsed.get("user_id")).first():
#                     print(f"✅ Valid response: {parsed}")
#                     return json.dumps(parsed)
#
#         except Exception as e:
#             print(f"⚠️ Attempt {attempt+1} failed: {str(e)}")
#
#     # Fallback with validation
#     candidates = filter_users_for_task(task, SampleUser.objects())
#     if candidates:
#         best_candidate = max(
#             [c for c in candidates if c[0].user_id != task.user_id],
#             key=lambda x: x[1]
#         )
#         return json.dumps({
#             "user_id": best_candidate[0].user_id,
#             "reason": "Fallback: Highest match score"
#         })
#
#     return json.dumps({"user_id": "U0000", "reason": "Assignment failed"})
#
#
#
# # Test with sample assignment prompt
# if __name__ == "__main__":
#     test_prompt = """Task Assignment Analysis:
# Task: API Gateway Implementation (T0022)
# Required Skills: ["python", "aws"]
# Candidates:
# - U0001 (skills: ["react"], workload: 1/4)
# - U0002 (skills: ["python", "aws"], workload: 2/5)"""
#
#     print("Testing enhanced LLM handler...")
#     response = query_mistral_llm(test_prompt)
#     print("\nFinal response:")
#     print(json.dumps(json.loads(response), indent=2))
