from llms.llm import LLM
from pydantic import BaseModel
from openai import OpenAI
import instructor
import json

class OpenAIClient(LLM):
    """
    OpenAI class for the file object
    """

    def __init__(self, config, models):
        super().__init__(provider="openai", config=config, models=models)
        
        self.client = OpenAI(api_key=config["OPENAI_API_KEY"])
        self.llm_instructor = instructor.patch(self.client)

    def prompt(self, prompt: str, model: str = "gpt-4o", schema:BaseModel=None):
        """
        Generate a response from the LLM
        """
        if model == "debug":
            return f"DEBUG LLM: {prompt[:50]}"

        if schema:
            return self.llm_instructor.chat.completions.create(
                model=self.get_model(model),
                messages=[{"role": "user", "content": prompt}],
                response_model=schema
            )

        response = self.client.chat.completions.create(
            model=self.get_model(model),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def stream_prompt(self, prompt: str, model: str = "gpt-4", llm_stream=None):
            """
            Stream a response from OpenAI
            """
            if model == "debug":
                return f"DEBUG LLM: {prompt[:50]}"

            response = ""
            stream = self.client.chat.completions.create(
                model=self.get_model(model),
                messages=[{"role": "user", "content": prompt}],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    text = chunk.choices[0].delta.content
                    response += text
                    if llm_stream:
                        llm_stream(text)

            return self.parse_response(response)