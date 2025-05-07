import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preload_model():
    """Pre-load the Llama model in Ollama"""
    model_name = "llama3:8b-instruct"  # Adjust if your model name is different
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt+1}: Pre-loading model {model_name}...")
            
            # Simple prompt to load the model
            response = requests.post(
                "http://ollama:11434/api/chat",
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say hello in one word."}
                    ],
                    "stream": False,
                    "options": {
                        "num_thread": 4
                    }
                },
                timeout=300  # 5 minute timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Model {model_name} successfully loaded!")
                return True
            else:
                logger.warning(f"Failed to load model: {response.text}")
                
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
        
        # Exponential backoff
        wait_time = 2 ** attempt
        logger.info(f"Waiting {wait_time} seconds before retrying...")
        time.sleep(wait_time)
    
    logger.error(f"Failed to pre-load model after {max_retries} attempts")
    return False

if __name__ == "__main__":
    preload_model()