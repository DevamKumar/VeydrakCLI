import os
from veydrak.tools import get_basic_tools

if __name__ == "__main__":
    # Define a test workspace directory
    ws = os.path.join(os.getcwd(), "workspace")
    
    # Ensure it exists just in case
    os.makedirs(ws, exist_ok=True)
    
    print(f"Initializing tools with workspace: {ws}\n")
    tools = get_basic_tools(ws)

    # The decorator turns the docstring and type hints into the schema the model sees.
    for t in tools:
        print(f"{t.name}: {t.description}")
        print(f" schema: {t.args_schema.model_json_schema()['properties']}\n")
