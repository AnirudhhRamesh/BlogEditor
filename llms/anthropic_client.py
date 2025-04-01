import json
import instructor
from anthropic import Anthropic
from pydantic import BaseModel
from llms.llm import LLM

import re
import json

class AnthropicClient(LLM):
    """
    Service class to interact with the LLM
    """

    def __init__(self, config, models):
        """
        Initialize the LLM service
        """
        super().__init__(provider="anthropic", config=config, models=models)
        self.client = Anthropic(api_key=config["ANTHROPIC_API_KEY"])
        self.llm_instructor = instructor.from_anthropic(Anthropic())

    def prompt(self, prompt: str, model: str = "sonnet", schema:BaseModel=None):
        """
        Generate a response from the LLM
        """
        if model == "debug":
            return f"DEBUG LLM: {prompt[:50]}"

        if schema:
            return self.llm_instructor.messages.create(
                model=self.get_model(model),
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_model=schema,
                max_tokens=4096
            )

        response = self.client.messages.create(
            model=self.get_model(model),
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

        response = ""
        with self.client.messages.stream(
            model=self.get_model(model),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096
        ) as stream:
            for text in stream.text_stream:
                response += text
                llm_stream(text)

        # TODO: Maybe I do 'post-processing' on the response to parse the JSON? I can't simultaneously stream and parse the JSON
        return self.parse_response(response)