"""
cruhon-discord-example
======================
Example mod showing how to write a namespace mod.
This is a TEMPLATE — not a real Discord bot.

To write a real Discord mod:
  1. Copy this structure
  2. Replace handlers with real discord.py calls
  3. pip publish as cruhon-discord
"""


def register(api):
    # Declare dependencies
    api.require("http")  # example dependency

    # Create namespace
    ns = api.namespace("discord")

    # Register lifecycle
    ns.hook("init", lambda n: n.state.update({"ready": True}))

    # Register methods
    ns.register("send",
        lambda args: f"[discord] send → {args[0] if args else ''}")

    ns.register("reply",
        lambda args: f"[discord] reply → {args[0] if args else ''}")

    ns.register("ban",
        lambda args: f"[discord] ban → user={args[0] if args else ''}"
                     f"{', reason=' + args[1] if len(args) > 1 else ''}")

    ns.register("embed",
        lambda args: f"[discord] embed → title={args[0] if args else ''}")
