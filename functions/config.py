"""
Configuration file for AI models and settings.
Change DEFAULT_MODEL to switch between different AI providers easily.
"""

# Available models
AVAILABLE_MODELS = {
    "gpt-4o": {
        "provider": "openai",
        "model_name": "gpt-4o",
        "max_tokens": 1000,
        "temperature": 0.1,
        "description": "OpenAI GPT-4o - Good for general analysis"
    },
    "claude-3-5-sonnet": {
        "provider": "anthropic", 
        "model_name": "claude-3-5-sonnet-20241022",
        "max_tokens": 1000,
        "temperature": 0.1,
        "description": "Anthropic Claude 3.5 Sonnet - Excellent for architectural drawings"
    }
}

# Default model - change this to switch models easily
DEFAULT_MODEL = "claude-3-5-sonnet"

# API Key environment variables
API_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY"
}

def get_model_config(model_name: str = None):
    """Get model configuration"""
    if model_name is None:
        model_name = DEFAULT_MODEL
    
    if model_name not in AVAILABLE_MODELS:
        raise ValueError(f"Unknown model '{model_name}'. Available models: {list(AVAILABLE_MODELS.keys())}")
    
    return AVAILABLE_MODELS[model_name]
