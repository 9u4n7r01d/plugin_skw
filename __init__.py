import lightbulb

from .skw import skw

__plugin_name__ = skw.name
__plugin_description__ = skw.description


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(skw)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(skw)
