import os
import torch
import re
import json
import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer

class CLI_Agent:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.tokenizer = self.load_model()
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "trace.jsonl")
    
    def load_model(self):
        model_path = "tinyllama_lora_adapter"
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model directory not found: {model_path}")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto" if self.device == "cuda" else None,
            torch_dtype=torch.float32
        )
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        tokenizer.pad_token = tokenizer.eos_token
        
        return model, tokenizer
    
    def format_prompt(self, user_prompt):
        return (
            f"<|system|>\nYou are a CLI expert assistant. Generate ONLY step-by-step shell commands without explanations.</s>\n"
            f"<|user|>\n{user_prompt}</s>\n"
            f"<|assistant|>\n"
        )
    
    def generate_plan(self, prompt):
        formatted_prompt = self.format_prompt(prompt)
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt", return_attention_mask=False).to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.1,  
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.2,
            pad_token_id=self.tokenizer.eos_token_id
        )
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        
        response = full_response.split("<|assistant|>")[-1].strip()
        return self.clean_response(response)
    
    def clean_response(self, response):
        """Extract only command lines from the response"""
        
        command_lines = []
        for line in response.split('\n'):
            line = line.strip()
            if self.is_shell_command(line):
                
                if '#' in line:
                    line = line.split('#')[0].strip()
                command_lines.append(line)
        
        return '\n'.join(command_lines)
    
    def is_shell_command(self, text):
        """Check if text looks like a shell command"""
        patterns = [
            r'^\s*[a-z]{2,}',  
            r'^\s*\w+\s+',       
            r'[\$\.\/~]',        
            r'-{1,2}[a-zA-Z]'    
        ]
        return any(re.search(pattern, text) for pattern in patterns) and not text.startswith(('I ', 'You ', 'We '))
    
    def dry_run_execute(self, command_line):
        """Simulate command execution in dry-run mode"""
        command_line = command_line.strip()
        
        
        if command_line.startswith(('$', '>')):
            command_line = command_line[1:].strip()
        
        return f"echo {command_line}"
    
    def process_instruction(self, instruction):
        """Process a single instruction and return results"""
        
        plan = self.generate_plan(instruction)
        
        
        executed_command = None
        for line in plan.split('\n'):
            line = line.strip()
            if line and self.is_shell_command(line):
                executed_command = self.dry_run_execute(line)
                break
        
        
        self.log_to_file({
            "timestamp": datetime.datetime.now().isoformat(),
            "instruction": instruction,
            "plan": plan,
            "executed_command": executed_command
        })
        
        return {
            "plan": plan,
            "executed_command": executed_command
        }
    
    def log_to_file(self, entry):
        """Append log entry to JSONL file"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def run_from_cli(self):
        """Run agent from command line interface"""
        import sys
        if len(sys.argv) < 2:
            print("Usage: python agent.py \"your natural language instruction\"")
            return
        
        instruction = " ".join(sys.argv[1:])
        print(f"\nProcessing instruction: {instruction}")
        
        result = self.process_instruction(instruction)
        
        print("\nGenerated Plan:")
        print(result['plan'])
        
        if result['executed_command']:
            print("\nDry-run Execution:")
            print(result['executed_command'])
        else:
            print("\nNo executable command found in plan")
        
        print(f"\nLogged to {self.log_file}")

if __name__ == "__main__":
    agent = CLI_Agent()
    agent.run_from_cli()