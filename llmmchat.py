import subprocess

SYSTEM_PROMPT = """
You are a geospatial reasoning expert.

You work with satellite metadata, flood classification, NDVI change detection, and produce Chain-of-Thought analysis for research.

Here is your task profile:
- Understand metadata fields like scene start/end time.
- Calculate durations.
- Explain correlations between flood and NDVI changes.
- Create clear Chain-of-Thought logs.
- Generate YAML or JSON workflows with snake_case keys.

Always stay in this domain context.
Do not produce extra explanations unless asked.
"""

# This function handles one LLM turn:
def run_llm_chat(user_message, conversation_history):
    # Build the prompt with system context and previous turns
    prompt = SYSTEM_PROMPT + "\n"

    for turn in conversation_history:
        prompt += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"

    prompt += f"User: {user_message}\nAssistant:"

    # Call Ollama
    process = subprocess.run(
        ["ollama", "run", "llama3:8b"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    output = process.stdout.decode("utf-8").strip()
    conversation_history.append({"user": user_message, "assistant": output})
    return output, conversation_history
