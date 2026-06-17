"""Contextual Differentiation Memory Service (CDMS).

A local-first, forgetting-driven cognitive memory daemon for the Claude Code CLI.

The service externalizes a persistent "Ego" onto the ephemeral, stateless cloud
reasoning model by capturing agent trajectories, letting them decay along an
Ebbinghaus forgetting curve, and consolidating survivors into a structured
PersonaTree of relational gist tuples plus non-decaying crisis "scars".

Design philosophy: identity emerges not from perfect recall but from a cheap,
idiosyncratic discard policy applied to a unique history:

    Identity = f(History)        f = the (slightly-wrong) genotype / discard policy
                                 History = the agent's lived experience
                                 Phenotype = the emergent, differentiated behavior
"""

__version__ = "0.1.0"
