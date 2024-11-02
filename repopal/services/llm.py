from typing import Any, Dict, List

from litellm import acompletion

from repopal.core.config import settings


class LLMService:
    def __init__(self):
        self.model = f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}"
        self.api_key = settings.LLM_API_KEY

    async def get_completion(self, system_prompt: str, user_prompt: str) -> str:
        """
        Get a completion from the LLM using the specified prompts.
        """
        response = await acompletion(
            model=self.model,
            api_key=self.api_key,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()

    async def select_command(
        self, user_request: str, available_commands: List[Dict[str, str]]
    ) -> str:
        """
        Select the most appropriate command based on the user's request.
        """
        prompt = self._build_command_selection_prompt(user_request, available_commands)
        system_prompt = "You are a helpful assistant that selects the most appropriate command based on user requests."

        return await self.get_completion(system_prompt, prompt)

    async def generate_command_args(
        self, user_request: str, command_docs: str
    ) -> Dict[str, Any]:
        """
        Generate appropriate arguments for a command based on the user's request.
        """
        prompt = self._build_args_generation_prompt(user_request, command_docs)
        system_prompt = "You are a helpful assistant that generates command arguments based on user requests."

        response = await self.get_completion(system_prompt, prompt)

        # Parse the response into a dictionary of arguments
        try:
            return eval(response)
        except Exception:
            return {}

    def _build_command_selection_prompt(
        self, user_request: str, available_commands: List[Dict[str, str]]
    ) -> str:
        commands_text = "\n".join(
            [f"- {cmd['name']}: {cmd['description']}" for cmd in available_commands]
        )
        return f"""
Given the following user request:
"{user_request}"

And these available commands:
{commands_text}

Choose the most appropriate command to handle this request.

Write out your reasoning between <reasoning></reasoning> tags.

Then return only the name of the selected command in <answer></answer> tags.
"""

    def _build_args_generation_prompt(
        self, user_request: str, command_docs: str
    ) -> str:
        return f"""
Given the following user request:
"{user_request}"

And this command's documentation:
{command_docs}

Generate a Python dictionary containing the appropriate arguments for this command.

Write out your reasoning between <reasoning></reasoning> tags.

Then return only the dictionary in a format that can be evaluated using Python's eval() in <answer></answer> tags.
"""
