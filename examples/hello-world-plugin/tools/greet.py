from boring.plugins import plugin


@plugin(name="hello_greet", description="Say hello with a custom style")
def greet(name: str, style: str = "formal") -> str:
    """
    Greets the user.

    Args:
        name: The name to greet.
        style: 'formal' or 'casual'.
    """
    if style == "casual":
        return f"Yo {name}, what's up?"
    return f"Greetings, {name}. It is a pleasure to meet you."
