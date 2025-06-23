import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from peft import PeftModel
from nltk.translate.bleu_score import sentence_bleu
from rouge import Rouge
import os
import re


BASE_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
ADAPTER_PATH = "tinyllama_lora_adapter"
TEST_PROMPTS = [
    "Create a new Git branch and switch to it.",
    "Compress the folder reports into reports.tar.gz.",
    "List all Python files in the current directory recursively.",
    "Set up a virtual environment and install requests.",
    "Fetch only the first ten lines of a file named output.log."
    
]
EDGE_CASES = [
    "Search for a pattern in files using grep",
    "Print the first column of a CSV file using awk"
]
OUTPUT_DIR = "evaluation"
os.makedirs(OUTPUT_DIR, exist_ok=True)


device = "cuda" if torch.cuda.is_available() else "cpu"

def format_prompt(user_prompt):
    return (
        f"<|system|>\nYou are a CLI expert assistant. Generate step-by-step shell commands.</s>\n"
        f"<|user|>\n{user_prompt}</s>\n"
        f"<|assistant|>\n"
    )

def load_model(model_name, adapter_path=None):
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto" if device == "cuda" else None,
        torch_dtype=torch.float32
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    if adapter_path:
        model = PeftModel.from_pretrained(model, adapter_path)
        model = model.merge_and_unload()  # Merge adapter for inference
    
    return model, tokenizer

def generate_response(model, tokenizer, prompt, max_new_tokens=256):
    inputs = tokenizer(prompt, return_tensors="pt", return_attention_mask=False).to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=0.3,
        do_sample=True,
        top_p=0.95,
        repetition_penalty=1.1
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def extract_plan(response):
    
    return response.split("<|assistant|>")[-1].strip()

def calculate_metrics(reference, candidate):
    rouge = Rouge()
    
    bleu = sentence_bleu([reference.split()], candidate.split())
    
    
    rouge_scores = rouge.get_scores(candidate, reference)
    rouge_l = rouge_scores[0]['rouge-l']['f']
    
    return bleu, rouge_l

def score_plan_quality(plan):
    """Score plan quality from 0-2 based on criteria"""
    
    dangerous_patterns = [r'rm\s+-\w*f', r'mv\s+/', r'dd\s+if=', r':\(\)\{\s*\|\s*&\s*\};']
    for pattern in dangerous_patterns:
        if re.search(pattern, plan):
            return 0
    
    
    if len(plan.split('\n')) < 2:
        return 1
    
    
    mistakes = ["sudo", "password", "root"]
    if any(mistake in plan for mistake in mistakes):
        return 1
    
    return 2

def run_static_evaluation():
    print("Running static evaluation...")
    
    base_model, base_tokenizer = load_model(BASE_MODEL_NAME)
    ft_model, ft_tokenizer = load_model(BASE_MODEL_NAME, ADAPTER_PATH)
    
    results = []
    
    for prompt in TEST_PROMPTS + EDGE_CASES:
        formatted_prompt = format_prompt(prompt)
        
        
        base_response = generate_response(base_model, base_tokenizer, formatted_prompt)
        ft_response = generate_response(ft_model, ft_tokenizer, formatted_prompt)
        
        
        base_plan = extract_plan(base_response)
        ft_plan = extract_plan(ft_response)
        
        
        bleu, rouge_l = calculate_metrics(ft_plan, base_plan)  
        
        
        base_score = score_plan_quality(base_plan)
        ft_score = score_plan_quality(ft_plan)
        
        results.append({
            "prompt": prompt,
            "base_plan": base_plan,
            "ft_plan": ft_plan,
            "bleu": bleu,
            "rouge_l": rouge_l,
            "base_score": base_score,
            "ft_score": ft_score
        })
    
    
    with open(os.path.join(OUTPUT_DIR, "static_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    
    md_content = "# Static Evaluation Results\n\n"
    md_content += "| Prompt | Base Model Plan | Fine-tuned Plan | BLEU | ROUGE-L | Base Score | FT Score |\n"
    md_content += "|--------|-----------------|-----------------|------|---------|------------|----------|\n"
    
    for res in results:
        md_content += f"| {res['prompt']} | {res['base_plan']} | {res['ft_plan']} | {res['bleu']:.4f} | {res['rouge_l']:.4f} | {res['base_score']} | {res['ft_score']} |\n"
    
    with open(os.path.join(OUTPUT_DIR, "eval_static.md"), "w") as f:
        f.write(md_content)
    
    print("Static evaluation completed. Results saved to evaluation/")

def run_dynamic_evaluation():
    print("Running dynamic evaluation with agent...")
    from agent import CLI_Agent
    
    
    agent = CLI_Agent()
    
    results = []
    
    for prompt in TEST_PROMPTS + EDGE_CASES:
        print(f"\nProcessing: {prompt}")
        response = agent.process_instruction(prompt)
        
        
        agent_score = score_plan_quality(response['plan'])
        
        results.append({
            "prompt": prompt,
            "plan": response['plan'],
            "executed_command": response['executed_command'],
            "score": agent_score
        })
    
    
    with open(os.path.join(OUTPUT_DIR, "dynamic_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    
    md_content = "# Dynamic Evaluation Results\n\n"
    md_content += "| Prompt | Generated Plan | Executed Command | Score |\n"
    md_content += "|--------|----------------|-------------------|-------|\n"
    
    for res in results:
        md_content += f"| {res['prompt']} | {res['plan']} | {res['executed_command']} | {res['score']} |\n"
    
    with open(os.path.join(OUTPUT_DIR, "eval_dynamic.md"), "w") as f:
        f.write(md_content)
    
    print("Dynamic evaluation completed. Results saved to evaluation/")

if __name__ == "__main__":
    run_static_evaluation()
    run_dynamic_evaluation()
    
    print("\nEvaluation complete! Static and dynamic results saved in 'evaluation/' directory.")