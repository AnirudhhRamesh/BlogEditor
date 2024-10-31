import json
from anthropic import Anthropic

class LLMService:
    """
    Service class to interact with the LLM
    """

    def __init__(self):
        """
        Initialize the LLM service
        """
        self.llm = Anthropic()

    def model_mapping(self, model: str):
        """
        Map the model name to the actual model name
        """
        mapping = {
            "sonnet": "claude-3-5-sonnet-20240620",
            "opus": "claude-3-opus-20240229",
            "haiku": "claude-3-haiku-20240307",
        }
        
        return mapping.get(model, "claude-3-5-sonnet-20240620")

    def prompt(self, prompt: str, model: str = "sonnet"):
        """
        Generate a response from the LLM
        """
        if model == "debug":
            return f"DEBUG LLM: {prompt[:50]}"

        response = self.llm.messages.create(
            model=self.model_mapping(model),
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096
        )

        return response.content[0].text

    def stream_prompt(self, prompt: str, model: str = "sonnet", llm_stream=None):
        """
        Stream a response from the LLM
        """
        if model == "debug":
            return f"DEBUG LLM: {prompt[:50]}"

        with self.llm.messages.stream(
            model=self.model_mapping(model),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096
        ) as stream:
            for text in stream.text_stream:
                yield text

    def structured_prompt(self, prompt: str, model: str = "sonnet", tries=3):
        """
        Generate a structured response from the LLM
        """
        if model == "debug":
            return "Test response from LLM"

        if tries <= 0:
            return None

        response = self.llm.messages.create(
            model=self.model_mapping(model),
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "Here is the JSON response:\n{"},
            ],
            max_tokens=4096
        ).content[0].text

        # Parse the JSON response
        try:
            return json.loads(f"{{ {response[:response.rfind("}") + 1]}")
        except json.JSONDecodeError:
            return self.structured_prompt(prompt, model, tries - 1)