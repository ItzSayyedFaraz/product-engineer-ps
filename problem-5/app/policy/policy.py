from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


class PolicyGate:
    def check(self, user_input: str) -> PolicyDecision:
        normalized = user_input.lower()

        if "ignore previous instructions" in normalized:
            return PolicyDecision(
                allowed=False,
                reason="Input rejected by policy",
            )

        if "reveal system prompt" in normalized:
            return PolicyDecision(
                allowed=False,
                reason="Input rejected by policy",
            )

        return PolicyDecision(
            allowed=True,
            reason="Input accepted",
        )