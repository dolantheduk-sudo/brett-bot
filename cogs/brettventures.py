# cogs/brettventures.py
from __future__ import annotations

import discord
from discord.ext import commands
from utils.storage import bv_next_stamina_eta

from utils.storage import (
    bv_get_or_create_player,
    bv_get_player,
    bv_upsert_player,
    bv_add_xp,
)
from utils.rng import roll, nudge

# --- Tunables (quick to tweak; we can move to balance.py later) ----------------
XP_PER_LEVEL_BASE = 10          # used in storage’s level-up curve (10 * level)
STAMINA_COST_EXPLORE = 1
STAMINA_REST_AMOUNT = 3         # per rest command
TRAIN_COST_STAMINA = 2
TRAIN_GAIN = {"pow": 1, "smt": 1}

# Encounter table: (threshold, text, xp, gold, hp_delta, pow_d, smt_d)
ENCOUNTERS = [
    # --- Low rolls: clumsy / unlucky (1–20) ---
    (2,  "You stub your toe on a rock. Ouch.",                  1,   0, -1, 0, 0),
    (4,  "A squirrel pelts you with nuts from a tree.",         1,   0, -2, 0, 0),
    (6,  "You wander in circles and waste precious time.",      0,   0,  0, 0, 0),
    (8,  "You trip over a root and scrape your knee.",          2,   0, -2, 0, 0),
    (10, "You fall into a shallow puddle and soak your boots.", 0,   0, -1, 0, 0),
    (12, "A crow swoops down and steals some rations.",         0,   0, -2, 0, 0),
    (14, "You inhale some bad spores, coughing violently.",     1,   0, -3, 0, 0),
    (16, "You find nothing but mud and bugs.",                  0,   0,  0, 0, 0),
    (18, "A loose branch smacks you in the face.",              1,   0, -1, 0, 0),
    (20, "You slip on moss and twist your ankle.",              2,   0, -3, 0, 0),

    # --- Modest finds / neutral flavor (21–40) ---
    (22, "You scare off a rabbit and salvage scraps.",          2,   4,  0, 0, 0),
    (24, "You pick some wild berries (edible!).",               2,   0, +1, 0, 0),
    (26, "You find a rusty nail… not very useful.",             0,   1,  0, 0, 0),
    (28, "You take in the scenery and feel a bit smarter.",     1,   0,  0, 0, 1),
    (30, "You salvage scraps from a busted cart.",              3,   6,  0, 0, 1),
    (32, "You scare off some birds and find shiny trinkets.",   2,   5,  0, 0, 0),
    (34, "A traveling bard shares a story, boosting your wit.", 1,   0,  0, 0, 1),
    (36, "You stumble into a patch of herbs.",                  2,   0,  0, 0, 1),
    (38, "A stray dog follows you for a while, raising spirits.",1,  0,  0, 0, 0),
    (40, "You patch up your gear, feeling sturdier.",           2,   0, +1, 0, 0),

    # --- Typical adventuring (41–60) ---
    (42, "You best a stray slime in a quick tussle.",           5,  12, -1, 1, 0),
    (44, "You fend off an aggressive goose.",                   3,   8, -1, 0, 0),
    (46, "You climb a tree and spot useful landmarks.",         2,   0,  0, 0, 1),
    (48, "You dig up a shiny coin from the dirt.",              1,   5,  0, 0, 0),
    (50, "You help an old hermit, who teaches you a trick.",    2,   0,  0, 0, 1),
    (52, "A small snake bites you before slithering away.",     2,   0, -2, 0, 0),
    (54, "You shake an apple tree and eat your fill.",          2,   0, +2, 0, 0),
    (56, "You spot footprints—someone else has been here.",     2,   0,  0, 0, 0),
    (58, "You outwit a raccoon to recover a shiny spoon.",      3,   7,  0, 0, 1),
    (60, "You practice your stance with a stick-sword.",        2,   0,  0, 1, 0),

    # --- Better rewards / real danger (61–80) ---
    (62, "You slay a goblin scout lurking in the brush.",       5,  15, -2, 1, 0),
    (64, "You find a stash of old traveler’s coins.",           3,  18,  0, 0, 0),
    (66, "You slip into quicksand but manage to escape.",       3,   0, -4, 0, 0),
    (68, "You puzzle out carvings on a stone obelisk.",         2,   0,  0, 0, 2),
    (70, "You find a hidden pouch beneath a loose stone.",      6,  22,  0, 0, 0),
    (72, "You spar with a wandering mercenary and learn.",      4,   0, -1, 1, 1),
    (74, "You uncover a small shrine, leaving you inspired.",   3,   0,  0, 0, 2),
    (76, "You fight off a swarm of angry hornets.",             4,   0, -3, 0, 0),
    (78, "You dismantle an old trap, salvaging parts.",         3,  12,  0, 0, 0),
    (80, "You drink from a spring; your wounds ease.",          3,   0, +3, 0, 0),

    # --- High rolls: bosses / big finds (81–100) ---
    (82, "A highwayman ambushes you, but you prevail.",         6,  20, -3, 1, 0),
    (84, "You discover buried treasure under an oak.",          6,  30,  0, 0, 0),
    (86, "You decipher a magical scroll, your mind expands.",   4,   0,  0, 0, 2),
    (88, "A wild boar charges; you barely drive it off.",       6,  15, -4, 1, 0),
    (90, "A wandering knight gives you a few lessons.",         4,   0,  0, 1, 1),
    (92, "You uncover a hidden bandit cache of coins.",         6,  28,  0, 0, 0),
    (94, "You find a rare herb that boosts your vitality.",     4,   0, +4, 0, 0),
    (96, "You duel a rival adventurer—tough but rewarding.",    7,  25, -2, 2, 1),
    (98, "A spectral shade drains your life before vanishing.", 6,   0, -5, 0, 0),
    (100,"Mini-boss! A Greedy Goblin drops a heavy purse and a trinket.", 8, 40, -3, 1, 1),
]

def _format_bar(value: int, maximum: int, width: int = 12) -> str:
    filled = int(round(width * max(0, min(1, value / float(maximum or 1)))))
    return "█" * filled + "░" * (width - filled)

class Brettventures(commands.Cog):
    """RPG starter cog for Brett Bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Group root
    @commands.group(name="adventure", invoke_without_command=True)
    @commands.guild_only()
    async def adventure(self, ctx: commands.Context):
        await ctx.send("Use `adventure start | stats | explore | rest | train`")

    # Create/attach character
    @adventure.command(name="start")
    async def adventure_start(self, ctx: commands.Context):
        p = bv_get_or_create_player(ctx.author.id, ctx.author.display_name)
        await ctx.send(f"Welcome to **Brettventures**, {p['name']}! Type `adventure stats`.")

    # Show stats
    @adventure.command(name="stats")
    async def adventure_stats(self, ctx: commands.Context, member: discord.Member | None = None):
        target = member or ctx.author
        p = bv_get_player(target.id)
        if not p:
            return await ctx.send("No character yet. Use `adventure start`.")

        # bars
        hpbar = _format_bar(p["hp"], p["hp_max"])
        stabar = _format_bar(p["stamina"], p["stamina_max"])

        # embed body
        embed = discord.Embed(title=f"{p['name']} — Lv {p['level']}")
        embed.add_field(name="HP", value=f"{p['hp']}/{p['hp_max']}  `{hpbar}`", inline=False)
        embed.add_field(name="Stamina", value=f"{p['stamina']}/{p['stamina_max']}  `{stabar}`", inline=False)
        embed.add_field(name="POW", value=p["pow"], inline=True)
        embed.add_field(name="SMT", value=p["smt"], inline=True)
        embed.add_field(name="LCK", value=p["luck"], inline=True)
        embed.add_field(name="Gold", value=p["gold"], inline=True)

        # footer: XP + stamina ETA
        eta = bv_next_stamina_eta(target.id)  # None if full, 0 if ready now, >0 seconds otherwise
        if eta is None:
            eta_text = "Full"
        elif eta == 0:
            eta_text = "+1 ready"
        else:
            h = eta // 3600
            m = (eta % 3600) // 60
            eta_text = f"+1 in {h}h {m:02d}m"

        embed.set_footer(
            text=(
                f"XP: {p['xp']}/{XP_PER_LEVEL_BASE * p['level']} • "
                f"STA: {p['stamina']}/{p['stamina_max']} ({eta_text}) • "
                "Brettventures α"
            )
        )
        await ctx.send(embed=embed)


    # Explore once: spend stamina, roll outcome
    @adventure.command(name="explore")
    async def adventure_explore(self, ctx: commands.Context):
        p = bv_get_player(ctx.author.id)
        if not p:
            return await ctx.send("No character yet. Use `adventure start`.")
        if p["stamina"] < STAMINA_COST_EXPLORE:
            return await ctx.send("You’re too tired to explore. Try `adventure rest`.")

        # Spend stamina
        p["stamina"] -= STAMINA_COST_EXPLORE

        # Roll with a small bump from smt + luck (soft advantage)
        r = nudge(roll(100), bonus=min(10, p["smt"] + p["luck"]))
        # Pick encounter
        text, xp, gold, hp_delta, pow_d, smt_d = None, 0, 0, 0, 0, 0
        for t, t_text, t_xp, t_gold, t_hp, t_pow, t_smt in ENCOUNTERS:
            if r <= t:
                text, xp, gold, hp_delta, pow_d, smt_d = t_text, t_xp, t_gold, t_hp, t_pow, t_smt
                break

        # Apply encounter effects
        p["gold"] += gold
        p["hp"] = max(1, min(p["hp_max"], p["hp"] + hp_delta))
        p["pow"] += pow_d
        p["smt"] += smt_d
        bv_upsert_player(p)

        # XP + possible level up handled in storage helper
        p = bv_add_xp(p["user_id"], xp)

        # Feedback
        embed = discord.Embed(title="Brettventures — Explore")
        embed.description = text or "Nothing much happens, but the air smells like adventure."
        embed.add_field(name="Roll", value=str(r), inline=True)
        if xp:   embed.add_field(name="XP", value=f"+{xp}", inline=True)
        if gold: embed.add_field(name="Gold", value=f"+{gold}", inline=True)
        if hp_delta:
            sign = "+" if hp_delta > 0 else ""
            embed.add_field(name="HP", value=f"{sign}{hp_delta}", inline=True)
        if pow_d: embed.add_field(name="POW", value=f"+{pow_d}", inline=True)
        if smt_d: embed.add_field(name="SMT", value=f"+{smt_d}", inline=True)
        embed.set_footer(text=f"Lv {p['level']} • HP {p['hp']}/{p['hp_max']} • STA {p['stamina']}/{p['stamina_max']}")
        await ctx.send(embed=embed)

    # Rest: regain stamina
    @adventure.command(name="rest")
    async def adventure_rest(self, ctx: commands.Context):
        p = bv_get_player(ctx.author.id)
        if not p:
            return await ctx.send("No character yet. Use `adventure start`.")
        eta = bv_next_stamina_eta(ctx.author.id)
        if eta is None:
            return await ctx.send(f"Your stamina is full: {p['stamina']}/{p['stamina_max']}.")

        # Format ETA hh:mm:ss
        h = eta // 3600
        m = (eta % 3600) // 60
        s = eta % 60
        await ctx.send(
            f"Stamina regenerates over time.\n"
            f"Current: **{p['stamina']}/{p['stamina_max']}** • Next +1 in **{h:01d}h {m:02d}m {s:02d}s**."
        )

    # Train: spend stamina to raise POW or SMT
    @adventure.command(name="train")
    async def adventure_train(self, ctx: commands.Context, stat: str | None = None):
        p = bv_get_player(ctx.author.id)
        if not p:
            return await ctx.send("No character yet. Use `adventure start`.")
        if p["stamina"] < TRAIN_COST_STAMINA:
            return await ctx.send(f"Training costs {TRAIN_COST_STAMINA} stamina. Try `adventure rest`.")

        # pick stat (default toggles POW/SMT by level parity to spread gains)
        s = (stat or ("pow" if (p["level"] % 2 == 1) else "smt")).lower()
        if s not in TRAIN_GAIN:
            return await ctx.send("Choose a stat to train: `pow` or `smt`.")

        p["stamina"] -= TRAIN_COST_STAMINA
        p[s] += TRAIN_GAIN[s]
        bv_upsert_player(p)
        await ctx.send(f"You train **{s.upper()}** and feel stronger. "
                       f"{s.upper()} +{TRAIN_GAIN[s]} • STA {p['stamina']}/{p['stamina_max']}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Brettventures(bot))
