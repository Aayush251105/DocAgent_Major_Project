# Local DocAgent Usage

## New file: remove all docstrings

`tool/remove_all_docstrings.py` removes Python docstrings from a file or an
entire project folder.

Remove docstrings from the included test project without backups:

```bash
python3 tool/remove_all_docstrings.py data/raw_test_repo_simple
```

Preview changes without modifying files:

```bash
python3 tool/remove_all_docstrings.py --dry-run data/raw_test_repo_simple
```

## Generate docstrings with Ollama

Make sure Ollama is running, then run:

```bash
python3 generate_docstrings.py --repo-path data/raw_test_repo_simple --config-path config/agent_config.yaml
```

The local configuration uses `qwen2.5-coder:7b` through Ollama at
`http://localhost:11434/v1/`.
