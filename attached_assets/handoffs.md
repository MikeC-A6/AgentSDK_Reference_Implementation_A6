Handoffs
Handoffs let one agent delegate a conversation to another agent. This is useful when you have multiple specialized agents (e.g., a “Spanish-only” agent vs. “English-only” agent) or domain-specific agents (tech support vs. billing).

High-Level Flow
A parent (or “triage”) agent can see multiple sub-agent handoff targets.
The parent decides to invoke a “handoff tool” referencing a specific sub-agent.
The SDK switches to that sub-agent for subsequent steps until it finishes or delegates again.
Handoff example
from agents import Agent, AgentRunner, handoff

spanish_agent = Agent(name="spanish_agent", instructions="You only speak Spanish.")
english_agent = Agent(name="english_agent", instructions="You only speak English.")

triage_agent = Agent(
  name="triage_agent",
  instructions="Handoff to the appropriate agent based on language.",
  handoffs=[spanish_agent, english_agent],
)

out = await AgentRunner.run(triage_agent, ["Hola, ¿cómo estás?"])
# The conversation is handed off to spanish_agent.
# Final answer will be in Spanish.
Behind the scenes:

Each sub-agent is wrapped in a handoff(...) object, which exposes a tool like "handoff_spanish_agent".
If the parent agent calls that tool, the SDK shifts the active agent to spanish_agent.
Handoff Input and Filters
You can define arguments for the new agent, or filter conversation history passed along. For example, limiting how much context the sub-agent sees or storing info in your own callback.

Streaming
Streaming is used when you want partial or incremental output (like a real-time chat experience). Instead of AgentRunner.run(...), call AgentRunner.run_streamed(...) to get an async iterator of events.

Streaming mode example
from agents import Agent, AgentRunner

stream = AgentRunner.run_streamed(agent, ["Tell me a story"])

async for event in stream.stream_events():
  # event.delta often includes partial text or function call info
  print(event.delta, end="", flush=True)
print("\n--- done ---")
Events could include:

Partial text responses
Tool call argument deltas
Indications that a final answer was produced
The agent can still call multiple tools, produce partial messages, or do a handoff while streaming.

