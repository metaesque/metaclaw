# OpenClaw Buidout

## Collaborative Software Development

*   How do I develop code within OpenClaw?

*   I act as orchestrator instead of the orchestrator acting as orchestrator,
    and/or I act as software_orchestrator instead of the software_orchestrator
    doing so.

*   I want to have the capabilities of the software_orchestrator at my disposal,
    but its current SOUL.md doesn't support conversation/collaborative design,
    so do we modify SOUL.md or define a separate agent?

## Autonomous Software Development

*   I provide a high-level prompt of some project to be written, along with
    concrete examples of what should be produced. My software team goes off and
    works on the project when not busy with other things, until finished.

*   Need support for "do in background, allow interupts"

*   Projects to work one
    *   Meta(Oopl)
    *   Meta(DND)
    *   trawler: scheduled repeated parsing of urls with custom scripts into
        custom data
    *   Meta<Research>: constant learning
    *   Meta<Self>: Quantified Self (digital twin)
    *   Meta<Account>: All websites/accounts
    *   Meta<Comms>: email/telegram/discord
    *   Meta<Social>: youtube, tumblr, tiktok, etc.
    *   Meta<Finance>: income/expense tracking
    *   Meta<Agent>: dynamically evolve agents and teams of agents

## Meta<Research>: Integrated Research Platform

*   Provide topics for the research team to acquire initial and/or ongoing
    information about

*   User specifies what they want researched, the important dimensions to track,
    how to weight dimensions to get an overall ranking, how often the research
    is to be updated, etc. and then lets the research team do its thing

*   Examples
    *   Research all available walking pads, ranking by:
        *   price
        *   weight of device
        *   max weight of person
        *   max speed
        *   utility when travelling
            *   can fold
            *   can go on airplanes
        *   examples
            *   https://www.walkingpad.com/products/walkingpad-c2-foldable-walking-machine?variant=40860148727973
            *   https://www.walkingpad.com/products/walkingpad-a1-pro-foldable-treadmill?srsltid=AfmBOoqJvXAUIXQ7OTfRIskyQqCBKeLiZiRUKG6xaQ1NR2dz0pK9p5lz

## Meta<Self>: Digital Twin, Quantified Self

Formalized into $MC/workspace/src/projects/self, with the design doc
as docs/DESIGN.md.

## Meta<Account>: Integrated website/account management

*   Maintain a comprehensive list of EVERY website account
    *   how to login (email, username, password, 2FA, etc)
    *   scope of website (what issues does this website solve?)
        *   create vectors in OpenClaw so it can identify which website can
            solve a specific problem (e.g. renew vehicle registration, see my
            prescriptions, buy an item, etc)
    *   how to change password and 2FA settings
    *   how to close account
    *   how to delete account

*   List
    *   Albera eServices: https://eservices.alberta.ca/
    *   Alberta.ca:       https://account.alberta.ca/
    *   MyHealth:         https://myhealth.alberta.ca/

    *   Dexcom
        *   Data: https://clarity.dexcom.eu/i/#/overview
        *   Admin: https://account.dexcom.com/en-CA

## Meta<Comms>: Integrated Communication Channels

*   I have one or more accounts on every single communication channel
    (Email, Discord, Slack, Telegram, SMS, etc)
    *   an OpenClaw agent is assigned to monitor almost all streams, and to
        transfer messages from those streams to a central hub, where I can
        view and respond to those messages
    *   when I send a response, it gets delivered via the appropriate channel
        and account to that person's preferred communication channel

## Meta<Social>: Integrated Social Networking

*   The same kind of integration can happen for social media (facebook,
    instagram, bluesky, twitter, etc)
    *   I have an account on all social media sites
    *   An personal AI agent is assigned to each site, and monitors DMs to me,
        as well as general posts from others
    *   Allows my agents to build up a knowledge base for every
        friend/acquitance based on their social media presence

## Meta<Finance>: Track Everything Financial

*   parse bank/cc/investment statements to identify transactions
*   algorithmically/heuristically/LLmily establish category/subcategory for
    every transaction
*   distribute transactions across day ranges
*   visualize per day, per week, per month and per year break downs of
    transactions
*   produce reports useful for taxes each year

## Meta<Agent>: Self-Modifying Agent Hierarchy

OpenClaw allows individual agents to modify their markdown files (SOUL.md,
MEMORY.md, AGENTS.md, etc) as standard practice. However, I want to have the
software team (or some more specialized team) constantly looking at the
question of whether the current set of teams is optimal, whether new teams
should be added, whether members should be add or removed from teams, etc.

Various agents markdown files need to be updated whenever a team member is added
or removed (e.g. the `lead` and `orchestrator` team members need to know about
all members of the team). This is currently done by having an LLM update all
needed files, but a more structured approach may be useful (the set of agents
in a team is formalized in .json files, and a python script auto-generates
certain portions of certain markdown files. This way, any time an agent is
added, we can be assured that all other agent files that need modifying are
actually modified. Currently, agent files get out-fo-date and out-of-sync
quickly, with detrimental impacts on prompt quality.

## TODOs

*   Power down and get UPS installed
    *   won't have Kasa HP300 #2 until October
    *   plug following into Kasa (which goes into UPS)
        *   0: Shaw Router
        *   1: spark1
        *   2: spark2
        *   3: evo-x2
        *   4: k8 plus
        *   5: binardat switch

*   Get DGX Spark #1 set up and integrated into MetaClaw
*   Get DGX Spark #2 set up and linked/chained with DGX Spark #1

*   Start working on Meta<Self>

*   Get bin/power_kasa.py updated to support devices moving from port to
    port. Also support acquisition of power readings every N minutes or seconds
    and log this someplace

*   Get browser provider implemented and working
    *   want to be able to extract core text from amazon listings, youtube
        videos, wikipedia entries, etc.

*   Get pdf parsing working so we can move forward on Meta<Finance>

*   Close wellsfargo accounts?
*   Cancel Canada Amazon Prime before 2026-09-25
*   Look into amazon pharmacy
