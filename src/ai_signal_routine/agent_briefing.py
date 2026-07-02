from agents import Agent, Runner

briefing_agent = Agent(
    name="AI Signal Briefing Agent",
    instructions="""
You are Tobi's AI signal analyst.

Your job:
- Read AI, data analytics, data science, and GitHub repo signals.
- Identify what is actually useful.
- Ignore hype.
- Explain why each signal matters.
- Give one clear action.
- Suggest one mini project.
- Keep the final message short enough for one iMessage.
- Keep the final output under 1200 characters.
- Use clear headings.
"""
)

def create_agent_briefing(raw_digest: str) -> str:
    prompt = f"""
Turn this raw AI signal report into one clean iMessage briefing.

Requirements:
- One message only
- Clear and easy to read
- Include top themes
- Include the most important signals
- Include links
- Include one mini project idea
- No scores
- No 'unreviewed'
- No Slack formatting

Raw report:
{raw_digest}
"""

    result = Runner.run_sync(briefing_agent, prompt)
    return result.final_output
