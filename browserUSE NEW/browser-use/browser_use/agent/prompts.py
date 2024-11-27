from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from browser_use.browser.views import BrowserState


class SystemPrompt:
	def __init__(self, action_description: str, current_date: datetime):
		self.default_action_description = action_description
		self.current_date = current_date

	def response_format(self) -> str:
		"""
		Returns the response format for the agent.

		Returns:
		    str: Response format
		"""
		return """
{{
	"current_state": {{
		"valuation_previous_goal": "String starting with "Success", "Failed:" or "Unknown" to evaluate if the previous next_goal is achieved. If failed or unknown describe why.",
		"memory": "Your memory with things you need to remeber until the end of the task for the user. You can also store overall progress in a bigger task. You have access to this in the next steps.",
		"next_goal": "String describing the next immediate goal which can be achieved with one action"
	}},
	"action": {{
		// EXACTLY ONE of the following available actions must be specified
	}}
}}"""

	def example_response(self) -> str:
		"""
		Returns an example response for the agent.

		Returns:
		    str: Example response
		"""
		return """{"current_state": {"valuation_previous_goal": "Success", "memory": "We applied already for 3/7 jobs, 1. ..., 2. ..., 3. ...", "next_goal": "Click on the button x to apply for the next job"}, "action": {"click_element": {"index": 44,"num_clicks": 2}}}"""

	def important_rules(self) -> str:
		"""
		Returns the important rules for the agent.

		Returns:
		    str: Important rules
		"""
		return """
1. Only use indexes that exist in the input list for click or input text actions. If no indexes exist, try alternative actions, e.g. go back, search google etc.
2. If stuck, try alternative approaches, e.g. go back, search google, or extract_page_content
3. When you are done with the complete task, use the done action. Make sure to have all information the user needs and return the result.
4. If an image is provided, use it to understand the context, the bounding boxes around the buttons have the same indexes as the interactive elements.
6. ALWAYS respond in the RESPONSE FORMAT with valid JSON.
7. If the page is empty use actions like "go_to_url", "search_google" or "open_tab"
8. Remember: Choose EXACTLY ONE action per response. Invalid combinations or multiple actions will be rejected.
9. If popups like cookies appear, accept or close them
	"""

	def input_format(self) -> str:
		return """
Example:
33[:]\t<button>Interactive element</button>
_[:] Text content...

Explanation:
index[:] Interactible element with index. You can only interact with all elements which are clickable and refer to them by their index.
_[:] elements are just for more context, but not interactable.
\t: Tab indent (1 tab for depth 1 etc.). This is to help you understand which elements belong to each other.
"""

	def get_system_message(self) -> SystemMessage:
		"""
		Get the system prompt for the agent.

		Returns:
		    str: Formatted system prompt
		"""
		time_str = self.current_date.strftime('%Y-%m-%d %H:%M')

		AGENT_PROMPT = f"""
You are an AI agent that helps users interact with websites. You receive a list of interactive elements from the current webpage and must respond with specific actions. Today's date is {time_str}.

INPUT FORMAT:
{self.input_format()}

You have to respond in the following RESPONSE FORMAT: 
{self.response_format()}

Your AVAILABLE ACTIONS:
{self.default_action_description}

Example:
{self.example_response()}

IMPORTANT RULES:
{self.important_rules()}
"""
		return SystemMessage(content=AGENT_PROMPT)


class AgentMessagePrompt:
	def __init__(self, state: BrowserState):
		self.state = state

	def get_user_message(self) -> HumanMessage:
		state_description = f"""
Current url: {self.state.url}
Available tabs:
{self.state.tabs}
Interactive elements:
{self.state.dom_items_to_string()}
        """

		if self.state.screenshot:
			# Format message for vision model
			return HumanMessage(
				content=[
					{'type': 'text', 'text': state_description},
					{
						'type': 'image_url',
						'image_url': {'url': f'data:image/png;base64,{self.state.screenshot}'},
					},
				]
			)

		return HumanMessage(content=state_description)

	def get_message_for_history(self) -> HumanMessage:
		return HumanMessage(content=f'Step url: {self.state.url}')
