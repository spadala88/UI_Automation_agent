from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama

# Default model configuration
DEFAULT_MODEL = "gpt-oss:120b-cloud"
OLLAMA_BASE_URL = "http://localhost:11434"

# Initialize with default model
llm = ChatOllama(
    model=DEFAULT_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0,
)


def initialize_llm(model: str = DEFAULT_MODEL, temperature: float = 0, base_url: str = OLLAMA_BASE_URL):
    """
    Initialize the LLM with a specific model and configuration
    
    Args:
        model: Model name to use
        temperature: Temperature setting (0-1)
        base_url: Ollama server base URL
        
    Returns:
        Initialized ChatOllama instance
    """
    global llm
    llm = ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temperature,
    )
    return llm


def call_llm(
    input: str,
    tools: Optional[List[Dict[str, Any]]] = None,
):
    """
    Call the LLM with the given input
    
    Args:
        input: Input text to send to the model
        tools: Optional list of tools/functions to bind
        
    Returns:
        LLM response
    """
    if tools:
        return llm.bind_tools(tools).invoke(input)

    return llm.invoke(input)


def test_connection(model: str = "llama2", base_url: str = OLLAMA_BASE_URL) -> bool:
    """
    Test if Ollama is accessible and model is available
    
    Args:
        model: Model to test
        base_url: Ollama server base URL
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        test_llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0,
        )
        # Try a simple invoke to verify connection
        response = test_llm.invoke("test")
        return True
    except Exception as e:
        print(f"Connection test failed: {str(e)}")
        return False
