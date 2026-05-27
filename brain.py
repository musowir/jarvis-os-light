from llama_cpp import Llama

# Path to the downloaded model
MODEL_PATH = "./Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"

# Load the model (adjust n_ctx for longer memory, n_threads to max your CPU cores)
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,      # Context window size (how much conversation it remembers)
    n_threads=8,     # Use 8 CPU threads (Snapdragon 8 Gen 2 has 8 efficient cores)
    verbose=False
)

def ask_jarvis(prompt):
    """Send a prompt to the model and return its response."""
    # The model expects a specific chat format: <|im_start|>user ... <|im_end|><|im_start|>assistant
    formatted_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    
    output = llm(
        formatted_prompt,
        max_tokens=256,        # Limit response length
        temperature=0.7,       # Creativity (0 = strict, 1 = creative)
        stop=["<|im_end|>", "<|im_start|>"],  # Stop tokens
        echo=False
    )
    # Extract the generated text and strip whitespace
    return output['choices'][0]['text'].strip()

# Simple interactive loop – replace input() with your STT function later
print("Jarvis brain active. Type 'exit' to quit.")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    if not user_input.strip():
        continue
    
    response = ask_jarvis(user_input)
    print(f"Jarvis: {response}\n")
