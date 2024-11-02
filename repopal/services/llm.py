from typing import Any, Dict, List
import openai
from repopal.core.config import settings

class LLMService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL

    async def select_command(self, user_request: str, available_commands: List[Dict[str, str]]) -> str:
        """
        Select the most appropriate command based on the user's request.
        """
        prompt = self._build_command_selection_prompt(user_request, available_commands)
        
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that selects the most appropriate command based on user requests."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content.strip()

    async def generate_command_args(self, user_request: str, command_docs: str) -> Dict[str, Any]:
        """
        Generate appropriate arguments for a command based on the user's request.
        """
        prompt = self._build_args_generation_prompt(user_request, command_docs)
        
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates command arguments based on user requests."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response into a dictionary of arguments
        try:
            return eval(response.choices[0].message.content.strip())
        except Exception:
            return {}

    def _build_command_selection_prompt(self, user_request: str, available_commands: List[Dict[str, str]]) -> str:
        commands_text = "\n".join([f"- {cmd['name']}: {cmd['description']}" for cmd in available_commands])
        return f"""
Given the following user request:
"{user_request}"

And these available commands:
{commands_text}

Return only the name of the most appropriate command to handle this request.
"""

    def _build_args_generation_prompt(self, user_request: str, command_docs: str) -> str:
        return f"""
Given the following user request:
"{user_request}"

And this command's documentation:
{command_docs}

Generate a Python dictionary containing the appropriate arguments for this command.
Return only the dictionary in a format that can be evaluated using Python's eval().
"""
