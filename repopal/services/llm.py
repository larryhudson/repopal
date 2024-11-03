import re
from typing import Any, Dict, List

from litellm import acompletion

from repopal.core.config import settings
from repopal.schemas.changes import RepositoryChanges


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
        completion = response.choices[0].message.content.strip()
        return self._extract_answer(completion)

    async def select_command(
        self, user_request: str, available_commands: List[Dict[str, str]]
    ) -> str:
        """
        Select the most appropriate command based on the user's request.
        """
        prompt = self._build_command_selection_prompt(user_request, available_commands)
        system_prompt = "You are a helpful assistant that selects the most appropriate command based on user requests."

        response = await self.get_completion(system_prompt, prompt)
        return response

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

    async def generate_change_summary(
        self,
        user_request: str,
        command_name: str,
        command_output: str,
        changes: RepositoryChanges,
    ) -> str:
        """
        Generate a summary of the changes made by a command execution.

        Args:
            user_request: The original user request
            command_name: The name of the command that was executed
            command_output: The output from running the command
            changes: Dictionary containing git diff and untracked files

        Returns:
            A natural language summary of the changes
        """
        prompt = self._build_change_summary_prompt(
            user_request, command_name, command_output, changes
        )
        system_prompt = "You are a helpful assistant that summarizes code changes in clear, concise language."

        return await self.get_completion(system_prompt, prompt)

    def _build_change_summary_prompt(
        self,
        user_request: str,
        command_name: str,
        command_output: str,
        changes: RepositoryChanges,
    ) -> str:
        changes_text = []

        # Format tracked changes
        if changes.tracked_changes:
            tracked_text = "\n".join(
                f"File: {c.path}\nDiff:\n{c.diff}" for c in changes.tracked_changes
            )
            changes_text.append(f"Tracked Changes:\n{tracked_text}")

        # Format untracked changes
        if changes.untracked_changes:
            untracked_text = "\n".join(
                f"File: {c.path}\nContent:\n{c.content}"
                for c in changes.untracked_changes
            )
            changes_text.append(f"Untracked Files:\n{untracked_text}")

        changes_summary = "\n\n".join(changes_text) or "No changes detected"

        return f"""
Given the following information about changes made to a repository:

User's original request:
"{user_request}"

Command executed:
{command_name}

Command output:
{command_output}

Changes:
{changes_summary}

Write a clear, concise summary of the changes that were made.

Write out your analysis between <reasoning></reasoning> tags.

Then provide a natural language summary of the changes between <answer></answer> tags.
"""

    async def generate_status_message(self, stage: str, context: Dict[str, Any]) -> str:
        """
        Generate an appropriate status message for the current stage of processing.

        Args:
            stage: The current processing stage ('received', 'selected', 'completed')
            context: Relevant information for generating the message
        """
        prompts = {
            "received": f"""
Generate a friendly message acknowledging receipt of this request:
"{context.get('user_request', '')}"

The message should indicate we are processing it.

Write out your reasoning between <reasoning></reasoning> tags.
Then provide the message between <answer></answer> tags.
""",
            "selected": f"""
Generate a status update message indicating we have selected this command:
{context.get('command_name', '')}

With these arguments:
{context.get('command_args', {})}

To handle this request:
"{context.get('user_request', '')}"

Write out your reasoning between <reasoning></reasoning> tags.
Then provide the message between <answer></answer> tags.
""",
            "completed": f"""
Generate a completion message summarizing these changes:
{context.get('changes_summary', '')}

In response to this request:
"{context.get('user_request', '')}"

Write out your reasoning between <reasoning></reasoning> tags.
Then provide the message between <answer></answer> tags.
""",
        }

        system_prompt = (
            "You are a helpful assistant providing status updates on automated tasks."
        )
        return await self.get_completion(system_prompt, prompts[stage])

    def _extract_answer(self, text: str) -> str:
        """Extract the content between <answer></answer> tags."""
        match = re.search(r"<answer>(.*?)</answer>", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text  # Return original text if no tags found
