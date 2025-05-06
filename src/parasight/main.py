import asyncio

from agents import Runner
from dotenv import load_dotenv

from parasight.special_agents import screenshot_agent

load_dotenv()


async def _run():
    # Run the agent with a user query
    result = await Runner.run(
        screenshot_agent,
        input="Please identify the username and password fields and login button on https://titan-manager.streamingbuzz.com.",
    )
    print(result.final_output)


def main() -> None:
    asyncio.run(_run())
