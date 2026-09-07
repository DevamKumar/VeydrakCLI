from config import PAGE_TITLE, PAGE_ICON, MODEL
from chat import get_client, stream_response
import tkinter as tk


def main():
    print(f"Welcome to {PAGE_TITLE} {PAGE_ICON}")
    print(f"Using model: {MODEL}")

    messages = []
    client = get_client("demo-key")

    # Create the main application window
    root = tk.Tk()
    root.title("Chat Application")

    # Create a sidebar frame
    sidebar = tk.Frame(root, width=300, bg='lightgrey')
    sidebar.pack(side='left', fill='y')

    # Create a text area for editing the system prompt
    prompt_text = tk.Text(sidebar, height=10, width=30)
    prompt_text.pack(pady=10)

    # Function to get user input and stream response
    def get_response():
        user_input = prompt_text.get("1.0", tk.END).strip()  # Get text from the text area
        messages.append({"role": "user", "content": user_input})
        for chunk in stream_response(client, messages):
            print(chunk)

    # Create a button to submit the prompt
    submit_button = tk.Button(sidebar, text="Submit Prompt", command=get_response)
    submit_button.pack(pady=10)

    # Start the GUI event loop
    root.mainloop()


if __name__ == "__main__":
    main()