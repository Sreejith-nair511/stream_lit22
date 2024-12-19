import ollama
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Set your Ollama API Key
ollama.api_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIX8uYFNgw2VK7HpZE/VsykA6gy5fVRElMG9RYckhq9K"

# Function to call the Ollama API
def get_response():
    return ollama.generate(
        model="llama3",  # Change to your desired model
        prompt="Hello"
    )

# Define the timeout duration in seconds (e.g., 30 seconds)
timeout_duration = 260 # seconds

# Start measuring time
start_time = time.time()

# Use ThreadPoolExecutor to run the request with a timeout
with ThreadPoolExecutor() as executor:
    future = executor.submit(get_response)

    try:
        # Wait for the response with a timeout
        response = future.result(timeout=timeout_duration)
        print(response)

    except TimeoutError:
        print(f"Request timed out after {timeout_duration} seconds.")
    
    except Exception as e:
        print(f"Error: {e}")

# Print the time it took to get a response
print(f"Response Time: {time.time() - start_time:.2f} seconds")
