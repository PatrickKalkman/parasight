# ui_test_agent.py
import asyncio
import os

from agents import Agent, Runner
from dotenv import load_dotenv

# --------------------------------------------------------------
from parasight.special_tools.analyze_image_with_omniparser_tool import analyze_image_with_omniparser
from parasight.special_tools.find_elements_tool import find_elements_by_description
from parasight.special_tools.interact_with_element_tool import interact_with_element_sequence

# ---- import your function_tools ------------------------------
from parasight.special_tools.take_screenshot_tool import take_screenshot
from parasight.special_tools.validate_element_exists_tool import validate_element_exists

# Construct the path to the .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
print(os.getenv("OPENAI_API_KEY"))


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
