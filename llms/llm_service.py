from llms.anthropic_client import AnthropicClient
from llms.openai_client import OpenAIClient
from llms.ollama_client import OllamaClient

import yaml
from pydantic import BaseModel

class LLMService:
    """
    LLM class for the file object
    """
    
    def __init__(self, config):
        # Load in the models config
        self.models = {}
        with open("llms/models.yaml", "r") as f:
            self.models = yaml.safe_load(f)

        self.anthropic = AnthropicClient(config, self.models)
        self.openai = OpenAIClient(config, self.models)
        self.ollama = OllamaClient(config, self.models)

        # Create a model router from the yaml file
        model_mapping ={
            "anthropic": self.anthropic,
            "openai": self.openai,
            "ollama" : self.ollama
        }

        self.model_router = {}
        for model, value in self.models.items():
            if value["provider"] in model_mapping:
                self.model_router[model] = model_mapping[value["provider"]]
            else:
                raise ValueError(f"Provider '{value["provider"]}' is not yet implemented")

    def _get(self, model: str):
        return self.model_router[model]

    def prompt(self, prompt: str, model: str = "sonnet", schema:BaseModel=None):
        client = self._get(model)
        return client.prompt(model=model, prompt=prompt, schema=schema)

    def stream_prompt(self, prompt: str, model: str = "sonnet", llm_stream=None):
        client = self._get(model)
        return client.stream_prompt(model=model, prompt=prompt, llm_stream=llm_stream)