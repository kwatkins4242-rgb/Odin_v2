# ODIN File Agent

Gives ODIN autonomous read/write access to your working directory via Gemini function calling.

## Setup

1. Drop this folder anywhere — recommended: `C:\AI\MyOdin\odin_agent\`

2. Install dependencies:
   ```
   pip install google-genai python-dotenv
   ```

3. Create a `.env` file in this folder (or in `C:\AI\MyOdin\`):
   ```
   GEMINI_API_KEY=your_key_here
   ```

4. (Optional) Override the working directory by setting env var:
   ```
   ODIN_WORK_DIR=C:\AI\MyOdin
   ```
   Default is already set to `C:\AI\MyOdin` in config.py.

## Usage

```bash
python main.py "Read odin_core.py and summarize what it does"
python main.py "Create a new file called test_hello.py that prints Hello ODIN"
python main.py "Find any files with broken imports and fix them" --verbose
```

`--verbose` shows token counts and raw function call results.

## What ODIN Can Do

| Tool | What it does |
|------|--------------|
| `get_files_info` | List files in any subdirectory |
| `get_file_content` | Read up to 10,000 chars of any file |
| `write_file` | Write complete files (creates dirs too) |
| `run_python_file` | Execute .py files and return output |

## Files

```
odin_agent/
├── main.py              # Entry point + agent loop
├── call_function.py     # Dispatches tool calls
├── get_files_info.py    # List directory tool
├── get_file_content.py  # Read file tool
├── write_file.py        # Write file tool
├── run_python.py        # Run Python tool
├── config.py            # WORKING_DIR, MAX_CHARS
└── prompts.py           # ODIN system prompt
```
