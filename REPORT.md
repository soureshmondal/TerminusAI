# Technical Evaluation Report: CLI Agent for Shell Command Generation

## Task Summary

The objective was to develop a lightweight, instruction-to-shell-command generation agent using an open-source small language model. The project involved:

- Finetuning a ≤2B parameter base model using QLoRA
- Simulating shell execution via dry-run commands
- Evaluating model performance through static and dynamic scoring
- Delivering a reproducible and modular codebase

---

## Data & Sources

- **Source**: Scraped programmatically from **Stack Overflow** using the official [Stack Exchange API](https://api.stackexchange.com/)
- **Tags Used**: "git", "bash", "grep", "awk", "sed", "curl", "wget", "tar", "gzip",
    "find", "chmod", "chown", "ssh", "scp", "makefile", "docker", "apt",
    "yum", "venv", "pip", "tmux", "zsh", "crontab".
- **Query Type**: Filtered for highly upvoted Q&A pairs related to CLI usage
- **Postprocessing**:
  - Filtered out incomplete, irrelevant, or verbose answers
  - Removed Q&A with <4 tokens or vague/non-command replies
  - Reformatted answers to enforce consistent, command-only style
- **Final Size**: 1,752 Q&A pairs used for fine-tuning
- **Format**: JSON (`question`, `answer` fields)


---

##  Model & Fine-Tuning

- **Base Model**: `TinyLlama-1.1B-Chat-v1.0`
- **Fine-Tuning**: QLoRA with PEFT adapter
- **Tokenizer**: AutoTokenizer from base model
- **Prompt Format**: ChatML-style (system/user/assistant tags)

### LoRA Hyperparameters

| Parameter        | Value                     |
|------------------|---------------------------|
| Rank (r)         | 16                        |
| Alpha            | 32                        |
| Dropout          | 0.05                      |
| Target Modules   | `["q_proj", "v_proj"]`    |
| Max Seq Length   | 1024                      |
| Trainable Params | 2.25M / 1.1B (0.204%)     |

---

## Training Summary

| Item                  | Value                  |
|-----------------------|------------------------|
| Runtime               | ~42 minutes            |
| Epochs                | 1                      |
| Samples Used          | 1,752                  |
| Batch Size            | 1 (with gradient accumulation) |
| Accelerator           | Google Colab (Free Tier) |
| GPU                   | Tesla T4 (16 GB VRAM)  |
| Frameworks            | HuggingFace Transformers, PEFT, Datasets |

---

##  Agent Behavior

- **Script**: `agent.py`
- Loads the fine-tuned model + adapter
- Formats input and generates shell steps using causal decoding
- Extracts and cleans commands via regex and heuristics
- Performs **dry-run** simulation via `echo`
- Logs full trace into `logs/trace.jsonl`

---

## Evaluation Summary

### Static Evaluation

- Compared base vs. fine-tuned outputs on 7 test prompts
- Scoring metrics:
  - **BLEU**: 0.043 (avg)
  - **ROUGE-L**: 0.33 (avg)
  - **Plan Quality Score**: `2/2` for all FT outputs

[`evaluation/eval_static.md`](evaluation/eval_static.md)

---

### Dynamic Evaluation

- Instructions executed via the actual agent interface
- Output plans scored for:
  - Accuracy
  - Usefulness
  - Safety

- Results:
  - 6 out of 7 = `2/2`
  - 1 out of 7 = `1/2` (minor format issue)

[`evaluation/eval_dynamic.md`](evaluation/eval_dynamic.md)

---

## Sample Output

**Prompt**: `Search for a pattern in files using grep`  
**Plan**:
```bash
grep -R --color=always "pattern" 
