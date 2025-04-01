import re
import json
from abc import ABC, abstractmethod
from pydantic import BaseModel

class LLM(ABC):

    @abstractmethod
    def __init__(self, provider: str, config, models: dict):
        self.provider = provider
        self.model_mapping = {}

        for key, value in models.items():
            if (value["provider"] == self.provider):
                self.model_mapping[key] = value["model"]

    def get_model(self, model: str):
        """
        Given the model alias, return the actual model name
        """
        if model in self.model_mapping:
            return self.model_mapping[model]
        else:
            raise ValueError(f"Model {model} not found in model mapping")

    @abstractmethod
    def prompt(self, prompt: str, model: str = "sonnet", schema:BaseModel=None):
        raise NotImplementedError("prompt() must be implemented by subclass")

    @abstractmethod 
    def stream_prompt(self, prompt: str, model: str = "sonnet", llm_stream=None):
        raise NotImplementedError("stream_prompt() must be implemented by subclass")

    def parse_response(self, response:str):
        """
        Parse a response string to extract JSON if present, otherwise return original string
        """

        response = response.strip()
        # Try to find JSON pattern {'response': '...'}
        match = re.search(r"\{[\s]*'response'[\s]*:[\s]*'([^']*)'[\s]*\}", response)
        
        if not match:
            print(f"No JSON found in response: {response}")
            return response
            
        try:
            # Try parsing the matched JSON string
            json_str = match.group(0).replace("'", '"')
            parsed = json.loads(json_str)
            return parsed['response']
        except:
            # If JSON parsing fails, return the matched string
            print(f"JSON parsing failed for response: {response}")
            return match.group(1)