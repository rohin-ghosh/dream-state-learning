"""
Dream-State agent package.

Exports the ReAct agent, its configuration dataclass, and the prompt builder.
"""

from dream_state.agent.react_agent import AgentConfig, ReActAgent, build_react_prompt

__all__ = [
    "AgentConfig",
    "ReActAgent",
    "build_react_prompt",
]
