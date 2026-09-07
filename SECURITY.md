# Security Policy

## API Key Handling

Veydrak requires an LLM provider API key (e.g., `OPENAI_API_KEY`).
- **Never** commit your `.env` file or hardcode your API key in source code.
- Veydrak reads keys exclusively from the environment.

## Execution Sandbox Limitations

Veydrak utilizes an isolated Python environment (`LocalSandbox`) to execute generated code for tests and self-correction loops.
- **This is NOT a secure OS-level sandbox.** It isolates standard library states and suppresses immediate side-effects, but it does NOT provide strict containerization or VM-level security.
- **Do NOT** use Veydrak to run completely untrusted or malicious arbitrary code.
- Veydrak runs tests against a "Scratch Workspace" copy of your files to protect your real project files from accidental data destruction during the generation phase.

## Responsible Disclosure

If you discover a security vulnerability within Veydrak, please do not disclose it publicly. Contact the maintainers directly via GitHub issues with the `Security` label.
