import logging

import hikari
import lightbulb
from lightbulb import context

import remi.core.checks
from remi.core.constant import Global
from remi.util.embed import create_info_embed

GUILD_ID = 300325789151526913


skw = lightbulb.Plugin("SKW", description="Various utility command for SKW", include_datastore=True)
skw.add_checks(remi.core.checks.limit_to_guild(GUILD_ID), lightbulb.checks.guild_only)

# Flags and cache
skw.d.cache_building = False
skw.d.cache_built = False

skw.d.event_buffer = []
skw.d.role_stats_cache = {
    670858915038232577: None,  # Badass Completionist
    894426991493800006: None,  # Badass BR Completionist
    417669841118298112: None,  # Bad Pistol Runner
    489499718489997322: None,  # No Weapon Runner
    353236380735897601: None,  # Classic Badass Completionist
    894426721728724992: None,  # Boss Rush Speedrunner
    700023422704681000: None,  # Speedrunner
    894426922757537872: None,  # Rush to Purity Completionist
    894426823566450739: None,  # Badass Rush to Purity Completionist
    894426481181196319: None,  # Boss Rush Speedrunner+
    740633559466901657: None,  # Speedrunner+
    438669777683349504: None,  # Badass Bad Pistol Runner
    489499631907110913: None,  # Badass No Weapon Runner
}


@skw.listener(hikari.events.MemberUpdateEvent)
async def on_member_update(event: hikari.events.MemberUpdateEvent):
    # We're assuming cache is built completely in terms of server member and statistics
    if skw.d.cache_building:
        skw.d.event_buffer.append(event)

    else:
        resolve_event(event)


def resolve_event(event: hikari.events.MemberUpdateEvent):
    old_roles = set(event.old_member.role_ids)
    new_roles = set(event.member.role_ids)

    removed = old_roles.difference(new_roles).intersection(skw.d.role_stats_cache.keys())
    added = new_roles.difference(old_roles).intersection(skw.d.role_stats_cache.keys())

    for role in removed:
        skw.d.role_stats_cache[role] -= 1

    for role in added:
        skw.d.role_stats_cache[role] += 1


def build_statistics_embed():
    return create_info_embed(
        title="Challenge role statistics",
        description="\n".join(
            [f"\N{BULLET} `{count or 0 :>5}` <@&{role_id}> " for role_id, count in skw.d.role_stats_cache.items()]
        ),
    )


@skw.command
@lightbulb.command("roles", description="Get total members with an obtainable run role.")
@lightbulb.implements(*Global.COMMAND_IMPLEMENTS)
async def soul_knight_wikia_roles(ctx: context.Context):
    if skw.d.cache_building:
        await ctx.respond(embed=create_info_embed("Statistics is being built, please retry later."))
        return

    if any(i is None for i in skw.d.role_stats_cache.values()) or not skw.d.cache_built:
        logging.info("Building role cache....")
        initial_respond = await ctx.respond(
            embed=create_info_embed("Building statistics, please wait. This should take around 30 seconds.")
        )

        # Set flags (process start)
        skw.d.cache_built = False
        skw.d.cache_building = True

        # Build the cache (initial run)
        target_role_ids = skw.d.role_stats_cache.keys()

        async for member in skw.bot.rest.fetch_members(GUILD_ID):
            for role_id in set(member.role_ids).intersection(target_role_ids):
                if skw.d.role_stats_cache[role_id] is None:
                    skw.d.role_stats_cache[role_id] = 0
                skw.d.role_stats_cache[role_id] += 1

            skw.app.cache.set_member(member)

        logging.info("Processing queued up events...")
        for event in skw.d.event_buffer:
            resolve_event(event)

        # Set flags (process stop)
        skw.d.cache_building = False
        skw.d.cache_built = True

        await initial_respond.edit(embed=build_statistics_embed())

    else:
        await ctx.respond(embed=build_statistics_embed())


@skw.command
@lightbulb.add_checks(lightbulb.checks.owner_only)
@lightbulb.command("clearcache", description="Clear cache status, forcing a rebuild next command")
@lightbulb.implements(*Global.COMMAND_IMPLEMENTS)
async def skw_clearcache(ctx: context.Context):
    skw.d.cache_built = False
    skw.d.role_stats_cache = {role_id: None for role_id in skw.d.role_stats_cache}
    await ctx.respond(embed=create_info_embed("Role statistics cache status cleared."))
