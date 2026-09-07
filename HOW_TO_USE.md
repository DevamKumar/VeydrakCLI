# How to Use Veydrak

This guide explains the practical day-to-step usage of the Veydrak Coding Agent.

## 1. Basic Usage

To start Veydrak, use the CLI and provide a feature request along with the target directory containing your codebase:

```bash
veydrak "Add a clear chat button to the UI" --dir ./my-project
```

## 2. Giving Instructions

Veydrak performs best with clear, high-level instructions. Instead of micromanaging files, describe the feature:
- **Good**: "Add a simple logging function to config.py"
- **Good**: "Add a conversation export button in the sidebar that saves chat history as a .txt file. Update config.py with available models."
- **Bad**: "Open app.py, go to line 45, and add `print(foo)`"

## 3. Planning

Once invoked, Veydrak enters the **Planning** phase. 
It uses Codebase RAG (grep, glob, reading files) to discover your project structure and existing conventions. It then outputs a structured `Plan` containing a list of `file_tasks` required to fulfill your instruction.

## 4. Code Generation

Veydrak maps over the `file_tasks` using LangGraph's `Send` API. This means if the plan requires editing 3 different files, Veydrak spawns 3 parallel code-generation nodes to execute the work concurrently.

## 5. Testing

Generated code is **never** applied directly to your repository immediately.
Instead, Veydrak copies your project into a temporary **Scratch Workspace**. It applies the generated code to the scratch files and automatically runs `python -m py_compile` and `pytest`.

## 6. Self-Correction

If tests fail, Veydrak automatically routes the traceback and errors back to the Code Generation node, instructing the LLM to fix the bug. It will retry this loop up to 3 times automatically.

## 7. AI Review

Once tests pass, the code enters the **AI Review** stage. A separate LLM evaluates the code for logic flaws, PEP-8 formatting, and type hints. If it rejects the code, it sends feedback back to Code Generation.

## 8. Human Approval

If the AI Review passes, execution freezes (`__interrupt__`). Veydrak prints the test results and a summary of the code. In an application interface, you would be presented with a diff to **Approve** or **Reject**. Rejections feed directly back into Code Generation with your comments.

## 9. Multi-Turn Workflows

Veydrak maintains conversation history (`MessagesState`). If you reject code, or simply provide follow-up instructions, Veydrak understands the context of the previous actions and adjusts accordingly.

## 10. Rules and Skills

Veydrak respects project-specific conventions:
- **Rules**: Place markdown files in `.cursor/rules/` (e.g. `python.mdc`). Veydrak will read these dynamically when modifying matching files.
- **Skills**: Specialized multi-step workflows.

## 11. Debugging & Time-Travel

Because Veydrak runs on LangGraph with `MemorySaver`, every action is checkpointed. Developers can inspect `agent.get_state_history(config)` to rewind execution, see exactly what the LLM generated at step 3, or branch execution to try a different approach. See `examples/ch18_time_travel_debug.py` for a demonstration.
