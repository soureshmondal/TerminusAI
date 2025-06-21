
# CLI Command Generation Agent (LoRA Fine-Tuning)

This project demonstrates the fine-tuning of a small language model (`TinyLlama-1.1B-Chat-v1.0`) using QLoRA to generate step-by-step shell commands from natural language instructions. The system includes simulated execution and evaluation via static and dynamic scoring.

---

## Features

- Fine-tunes a base model using LoRA (QLoRA)
- Custom dataset of CLI instructions and answers
- Agent (`agent.py`) that converts instructions into shell plans
- Dry-run shell command execution (via `echo`)
- Static evaluation using BLEU, ROUGE-L, and plan quality scoring
- Dynamic evaluation using the agent in a simulated environment
- Markdown and JSON reports + trace logs

---

## Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt


2. Data Scraping & Fine-Tuning
Open task.ipynb and execute:

Q&A scraping (if required)

Preprocessing and filtering

LoRA-based training and saving adapter to tinyllama_lora_adapter/

3. Run the CLI Agent

python agent.py "Create a tarball of a directory"
Outputs a step-by-step plan

Simulates the command using echo

4. Run Evaluations

python evaluate.py
Static Evaluation: BLEU, ROUGE-L, and heuristic score

Dynamic Evaluation: Via dry-run execution through agent.py

Results
Results stored in:

evaluation/eval_static.md

evaluation/eval_dynamic.md

Model Details
Component	Value
Base Model	TinyLlama-1.1B-Chat-v1.0
Adapter Type	QLoRA (LoRA with 4-bit)
Config	r=16, alpha=32
Training Data	7 filtered CLI Q&A pairs
Max Tokens	1024


Author
Souresh Mondal
MCA, Jadavpur University
AI/ML Internship Project — Fenrir Security Pvt Ltd
