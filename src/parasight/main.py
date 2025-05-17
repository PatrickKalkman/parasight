# ui_test_agent.py
import asyncio
import os

from agents import Agent, Runner, trace
from dotenv import load_dotenv

# --------------------------------------------------------------
from parasight.special_tools.analyze_image_with_omniparser_tool import analyze_image_with_omniparser
from parasight.special_tools.find_elements_tool import find_elements_by_description
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
    find_elements_by_description,
    validate_element_exists,
    interact_with_element_sequence,
]

agent = Agent(
    name="UITestAgent",
    instructions=(
        "You are a ruthless UI‑testing bot. "
        "Goal: prove the login flow works. "
        "1️⃣ Grab a screenshot. "
        "2️⃣ Use OmniParser to read labels. "
        "3️⃣ Find username, password, Login button. "
        "4️⃣ Click/type in order via interact_with_element_sequence. "
        "5️⃣ Declare PASS when redirected to dashboard, otherwise FAIL."
    ),
    tools=UITEST_TOOLS,
    model="gpt-4o-mini",
)


async def main():
    # Natural‑language task prompt – the agent plans the calls itself
    with trace("Running UI test agent..."):
        result = await Runner.run(
            agent,
            "Open http://192.168.1.28:3000 and run the login flow with "
            "username='demo' & password='password123'. "
            "Return PASS if redirected to /dashboard, else FAIL.",
        )
        print(result.final_output)
    # result.full_output gives you every intermediate tool call if you want traces


if __name__ == "__main__":
    asyncio.run(main())
