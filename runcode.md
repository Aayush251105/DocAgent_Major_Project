# Running DocAgent with Ollama

This guide explains how to run DocAgent locally with Ollama. DocAgent generates Python docstrings by parsing a target repository, building a dependency graph, and calling a local LLM through Ollama's OpenAI-compatible API.

Important: DocAgent edits the target Python files in place. Run it on a test copy or a Git branch before using it on important code.

## Recommended Model

Use this model for the best speed/quality balance on most local machines:

```powershell
ollama pull qwen2.5-coder:7b
```

For better quality, use `qwen2.5-coder:14b`, but it may be much slower if the model does not fit fully on your GPU.

You can check CPU/GPU usage while DocAgent is running:

```powershell
ollama ps
```

If the `PROCESSOR` column shows mostly CPU, use the 7B model for faster runs.

## First-Time Setup After Cloning from GitHub

Clone the repository and enter the project:

```powershell
git clone <repository-url>
cd DocAgent
```

Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Upgrade packaging tools and install the project:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

Install Ollama for Windows if it is not installed yet:

```text
https://ollama.com/download/windows
```

After installing Ollama, close and reopen the terminal, then verify:

```powershell
ollama --version
```

Pull the recommended model:

```powershell
ollama pull qwen2.5-coder:7b
```

Create the config file:

```powershell
Copy-Item config\example_config.yaml config\agent_config.yaml
```

Edit `config/agent_config.yaml` and use this Ollama config:

```yaml
llm:
  type: "ollama"
  api_key: "ollama"
  api_base: "http://localhost:11434/v1/"
  model: "qwen2.5-coder:7b"
  temperature: 0.1
  max_output_tokens: 1024
  max_input_tokens: 8000

rate_limits:
  ollama:
    requests_per_minute: 120
    input_tokens_per_minute: 1000000
    output_tokens_per_minute: 300000
    input_token_price_per_million: 0
    output_token_price_per_million: 0

flow_control:
  max_reader_search_attempts: 0
  max_verifier_rejections: 0
  status_sleep_time: 0

docstring_options:
  overwrite_docstrings: false
  max_lines: 6

perplexity:
  api_key: ""
  model: "sonar"
  temperature: 0.1
  max_output_tokens: 250
```

Run DocAgent on the included small test repository:

```powershell
python generate_docstrings.py `
  --repo-path data\raw_test_repo_simple `
  --config-path config\agent_config.yaml
```

Run DocAgent on the bigger included test repository:

```powershell
python generate_docstrings.py `
  --repo-path data\raw_test_repo `
  --config-path config\agent_config.yaml
```

## Running on a New Application After Setup

Use this section if you already installed dependencies and pulled the Ollama model.

Open the DocAgent project:

```powershell
cd C:\path\to\DocAgent
.\.venv\Scripts\Activate.ps1
```

Make sure Ollama can see the model:

```powershell
ollama list
```

Run DocAgent on your new Python application:

```powershell
python generate_docstrings.py `
  --repo-path C:\path\to\your\python\project `
  --config-path config\agent_config.yaml
```

For the first run on a new application, keep this setting:

```yaml
docstring_options:
  overwrite_docstrings: false
  max_lines: 6
```

This allows DocAgent to skip existing meaningful docstrings instead of replacing them.
`max_lines` keeps generated docstrings concise.

## Faster vs Better Settings

Fast testing settings:

```yaml
flow_control:
  max_reader_search_attempts: 0
  max_verifier_rejections: 0
  status_sleep_time: 0
```

Better quality settings:

```yaml
flow_control:
  max_reader_search_attempts: 1
  max_verifier_rejections: 1
  status_sleep_time: 0
```

Use `qwen2.5-coder:7b` for speed and `qwen2.5-coder:14b` for better output if your GPU can handle it.

## Web UI

Start the web interface:

```powershell
python run_web_ui.py
```

Open this URL:

```text
http://127.0.0.1:5000
```

Use these UI values:

```text
Type: Ollama
API Key: ollama
API Base URL: http://localhost:11434/v1/
Model: qwen2.5-coder:7b
Max Tokens: 1024
Max Input Tokens: 8000
```

For repository path in the web UI, prefer an absolute path such as:

```text
C:\Users\aayus\OneDrive\Desktop\SRS_DOC_Generation\DOC_Agent\DocAgent\data\raw_test_repo
```

## Troubleshooting

If `ollama` works in normal PowerShell but not in VS Code, restart VS Code. The terminal may have an old `PATH`.

If needed, run Ollama directly:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" --version
```

If dependency installation fails on Windows with a long-path error involving `torch`, use the normal install:

```powershell
python -m pip install -e .
```

Do not install CUDA/HuggingFace extras unless you are not using Ollama.

If a run is too slow, stop it with `Ctrl+C`, switch to `qwen2.5-coder:7b`, and set the fast flow-control values shown above.

If you rerun DocAgent on the same project, it should skip existing meaningful docstrings as long as `overwrite_docstrings` is `false`.
