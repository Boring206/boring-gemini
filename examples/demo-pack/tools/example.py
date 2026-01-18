from boring.plugins import plugin


@plugin(name="hello_world", description="Say hello")
def hello_world(name: str = "World"):
    return f"Hello, {name}!"
