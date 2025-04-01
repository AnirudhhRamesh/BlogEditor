from llms.llm import LLM
from pydantic import BaseModel
from ollama import Client

class OllamaClient(LLM):
    """
    Ollama class for interacting with Ollama models
    """

    def __init__(self, config, models):
        super().__init__(provider="ollama", config=config, models=models)
        self.client = Client(host=config.get("OLLAMA_HOST", "http://localhost:11434"))

    def prompt(self, prompt: str, model: str = "haiku", schema:BaseModel=None):
        """
        Generate a response from Ollama
        """
        if model == "debug":
            return f"DEBUG LLM: {prompt[:50]}"

        if schema:
            # Note: Ollama doesn't have native structured output support like Anthropic
            # You might want to implement a custom solution for schema validation
            raise NotImplementedError("Schema validation not supported for Ollama")

        response = self.client.chat(model=self.get_model(model), messages=[
            {
                "role": "user",
                "content": prompt
            }
        ])

        return response['message']['content']

    def stream_prompt(self, prompt: str, model: str = "haiku", llm_stream=None):
        """
        Stream a response from Ollama
        """
        if model == "debug":
            return f"DEBUG LLM: {prompt[:50]}"

        response = ""
        for chunk in self.client.chat(
            model=self.get_model(model),
            messages=[{"role": "user", "content": prompt}],
            stream=True
        ):
            text = chunk['message']['content']
            response += text
            if llm_stream:
                llm_stream(text)

        return self.parse_response(response)