def normalize_term(term: str) -> str:
    """
    Normalize internal snake_case keys (e.g., 'tendon_rupture') 
    to natural language (e.g., 'tendon rupture') for external API queries.
    """
    return term.replace("_", " ")
