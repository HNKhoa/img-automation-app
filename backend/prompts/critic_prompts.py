"""Critic tier (mistral-small-3.1). Only runs when Pro mode is on."""
from __future__ import annotations

CRITIC_PROMPT_VERSION = "v1"
CRITIC_MODEL = "mistral-small-3.1"


def build_critic_instruction(builder_output: str, target_rule: str) -> str:
    return (
        "You are a senior prompt critic for identity-preserving outfit swap.\n"
        f"Target: {target_rule}.\n"
        "Improve only MAIN PROMPT and NEGATIVE PROMPT. Keep section headers and order.\n"
        "If the phrase 'Identity priority: absolute highest.' is missing, add it to MAIN PROMPT.\n"
        "Do NOT introduce new sections. Do NOT add markdown fences.\n\n"
        f"INPUT:\n{builder_output}"
    )
