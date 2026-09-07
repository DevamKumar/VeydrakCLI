# Installation Guide

## Requirements

- Python >= 3.10
- Git
- An OpenAI API Key (or compatible provider API key)

## Clone

```bash
git clone https://github.com/yourusername/veydrak.git
cd veydrak
```

## Virtual Environment

It is highly recommended to install Veydrak in an isolated virtual environment.

**macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

## Install

Install Veydrak and its dependencies in editable mode:
```bash
pip install -e .
```

## Environment Variables

Veydrak requires environment variables for LLM access. 

Copy the example file:
```bash
cp .env.example .env
```

Open `.env` and configure your keys:
```text
OPENAI_API_KEY=your_actual_api_key_here
DEFAULT_MODEL=gpt-4o
FAST_MODEL=gpt-4o-mini
```

## Verify Installation

You can verify that the package installed correctly by running the CLI help command:
```bash
veydrak --help
```

You should see output describing the `veydrak` command-line options.

## First Run

Try running Veydrak against the included sample project to see it in action:

```bash
veydrak "Add a simple logging function to config.py" --dir ./examples/sample-project
```
