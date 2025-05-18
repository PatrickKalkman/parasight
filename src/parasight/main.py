# ui_test_agent.py
import asyncio
import os

from agents import Agent, Runner, trace
from dotenv import load_dotenv

# --------------------------------------------------------------
from parasight.special_tools.analyze_image_with_omniparser_tool import analyze_image_with_omniparser
from parasight.special_tools.interact_with_element_tool import interact_with_element_sequence

# ---- import your function_tools ------------------------------
from parasight.special_tools.take_screenshot_tool import take_screenshot
from parasight.special_tools.validate_element_exists_tool import validate_element_exists

# Construct the path to the .env file in the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
dotenv_path = os.path.join(project_root, ".env")

# Try to load from .env file
load_dotenv(dotenv_path)

# Check if OPENAI_API_KEY is set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print(f"Warning: OPENAI_API_KEY not found in {dotenv_path}")
    print("Please set your OPENAI_API_KEY in the .env file or as an environment variable")
    print("Example .env file content: OPENAI_API_KEY=your-api-key-here")
    raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file or environment.")
else:
    print(f"OPENAI_API_KEY loaded successfully from {dotenv_path}")


UITEST_TOOLS = [
    take_screenshot,
    analyze_image_with_omniparser,
    validate_element_exists,
    interact_with_element_sequence,
]

agent = Agent(
    name="UITestAgent",
    instructions=(
        "You are a meticulous UI testing agent. Your primary goal is to verify the login functionality of a web application."
        "Follow these steps precisely, using the provided tools and information from the user's prompt:"
        "1. Use `take_screenshot` to capture the initial state of the login page."
        "   The URL for the page will be provided in the user's task prompt."
        "2. Use `analyze_image_with_omniparser` with the `file_path` from step 1. This tool returns JSON data detailing all"
        "   visible elements, their text, type, and normalized (0-1 range) coordinates. Carefully review this output."
        "3. From the OmniParser JSON output (step 2), identify the 'username' input field, 'password' input field, and the"
        "   'Login' button. Match them using descriptions if provided in the prompt (e.g., 'enter your username')."
        "   Note their exact normalized (x, y) coordinates. These coordinates are crucial for the next step."
        "4. Use `interact_with_element_sequence` to perform the login. Construct the `interactions` list:"
        "   - For text fields: use normalized coordinates (step 3), action 'type', and credentials from prompt."
        "   - For the Login button: use its normalized coordinates from step 3 and action 'click' and wait for 2 seconds."
        "   Set `browser_state.url` to the login page URL. Ensure `take_screenshots` is effectively true."
        "5. The `interact_with_element_sequence` tool returns a list of results. From the result of the *final* interaction"
        "   (e.g., after clicking Login), extract the `screenshot_after_action`. This is a path to the file."
        "6. Use `analyze_image_with_omniparser` on this screenshot to get the OmniParser JSON output again."
        "7. Use `validate_element_exists` with the OmniParser JSON output from step 6. For `element_description`, use the"
        "   success message text provided in the user's prompt (e.g., 'successfully logged')."
        "8. Based on the boolean `element_exists` field in the `validate_element_exists` output: if true, the success"
        "   message was found, so your final answer is 'PASS'. Otherwise, your final answer is 'FAIL'."
        "Your final output to the user must be a single word: 'PASS' or 'FAIL'. Do not add any other explanations."
    ),
    tools=UITEST_TOOLS,
    model="gpt-4o-mini",
)


async def main():
    # Natural‑language task prompt – the agent plans the calls itself
    with trace("Running UI test agent..."):
        result = await Runner.run(
            agent,
            "Test the login flow for the application at http://192.168.1.28:3000. "
            "Use username 'demo' and password 'password123'. "
            "The username field is described by 'enter your username'. "
            "The password field is described by 'enter your password'. "
            "The login button is labeled 'Login'. "
            "The test passes if the page after login contains the success message: "
            "'successfully logged'. "
            "Otherwise, the test fails. Your final answer should be PASS or FAIL.",
        )
        print(result.final_output)
    # result.full_output gives you every intermediate tool call if you want traces


if __name__ == "__main__":
    asyncio.run(main())
