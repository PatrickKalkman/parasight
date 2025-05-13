# ui_test_agent.py

from agents import Agent

from parasight.special_tools.analyze_image_with_omniparser_tool import analyze_image_with_omniparser
from parasight.special_tools.find_elements_tool import find_elements_by_description
from parasight.special_tools.interact_with_element_tool import interact_with_element_sequence

# ---- import your function_tools ------------------------------
from parasight.special_tools.take_screenshot_tool import take_screenshot
from parasight.special_tools.validate_element_exists_tool import validate_element_exists

# --------------------------------------------------------------

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
    model="gpt-4o-mini",  # pick your weapon
    max_iterations=10,  # don’t loop forever
)
