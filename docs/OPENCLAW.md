# OpenClaw Buidout

## Collaborative Software Development

- How do I develop code within OpenClaw?

- I act as orchestrator instead of the orchestrator acting as orchestrator,
  and/or I act as software_architect instead of the software_architect doing
  so.

- I want to have the capabilities of the software_architect at my disposal, but
  its current SOUL.md doesn't support conversation/collaborative design, so do
  we modify SOUL.md or define a separate agent?

## Autonomous Software Development

- I provide a high-level prompt of some project to be written, along with
  concrete examples of what should be produced. My software team goes off and
  works on the project when not busy with other things, until finished.

- Need support for "do in background, allow interupts"

- Projects to work one
   - Meta(Oopl)
   - Meta(DND)
   - trawler: scheduled repeated parsing of urls with custom scripts into custom data
   - Meta<Research>: constant learning
   - Meta<Self>: Quantified Self (digital twin)
   - Meta<Account>: All websites/accounts
   - Meta<Comms>: email/telegram/discord
   - Meta<Social>: youtube, tumblr, tiktok, etc.
   - Meta<Finance>: income/expense tracking
   - Meta<Agent>: dynamically evolve agents and teams of agents

## Meta<Research>: Integrated Research Platform

- Provide topics for the research team to acquire initial and/or ongoing
  information about

- User specifies what they want researched, the important dimensions to track,
  how to weight dimensions to get an overall ranking, how often the research
  is to be updated, etc. and then lets the research team do its thing

- Examples
   - Research all available walking pads, ranking by:
      - price
      - weight of device
      - max weight of person
      - max speed
      - utility when travelling
         - can fold
         - can go on airplanes
      - examples
         - https://www.walkingpad.com/products/walkingpad-c2-foldable-walking-machine?variant=40860148727973
         - https://www.walkingpad.com/products/walkingpad-a1-pro-foldable-treadmill?srsltid=AfmBOoqJvXAUIXQ7OTfRIskyQqCBKeLiZiRUKG6xaQ1NR2dz0pK9p5lz


## Meta<Self>: Digital Twin, Quantified Self

### Overview

This project is my implementation of "Quantified self". From wikipedia,
Quantified self is both the cultural phenomenon of self-tracking with technology
and a community of users and makers of self-tracking tools who share an interest
in "self-knowledge through numbers".[1] Quantified self practices overlap with
the practice of lifelogging and other trends that incorporate technology and
data acquisition into daily life, often with the goal of improving physical,
mental, and emotional performance. The widespread adoption in recent years of
wearable fitness and sleep trackers such as the Fitbit or the Apple Watch,[2]
combined with the increased presence of Internet of things in healthcare and in
exercise equipment, have made self-tracking accessible to a large segment of the
population.

Other terms for using self-tracking data to improve daily functioning are
auto-analytics, body hacking, self-quantifying, self-surveillance, sousveillance
(recording of personal activity), and personal informatics.

### Data Sources and Streams

At the center of this project is the concept of data sources (what creates the
raw information) and data streams (canonicalized timeseries capturing a very
specific quantifiable metric).

Each data source stores raw information in source-specific formats, and one of
the purposes of this project is to take disparate input formats and place them
in a common timeseries format so that we can operate of all data streams using
the same code, and can compare trends/patterns across data streams.

The class `wmc.qs.DataSource` is an abstract superclass. Every data source is
represents by a subclass of this class. For example, all functionality related
to extracting all data that can be obtained from a Fitbit Charge 6 could be
encapsulated within the `wmc.qs.FitbitCharge6` subclass of `wmc.qs.DataSoruce`.
However, it is an open design question what the exact scope of wmc.qs.DataSource
subclasses could be:

 - `wmc.qs.FitbitCharge6` would be a data source that produces multiple data
   streams, one for heart rate, one for steps, one for calories burned, etc.
 - `wmc.qs.Fitbit` would be a data source that produces multiple data streams
   for multiple different Fitbit devices (Charge 6, Versa 4, Inspire 3, Sense 2,
   etc)
 - `wmc.qs.FitbitCharge6Heartrate` would be if we decide there should be one
   data source per stream (this would probably lead to repeated code in similar
   classes, so it is probably not the best architectural decision unless we
   introduce a richer class hierarchy including DataSourceFamily to capture
   these "similar classes").

The `wmc.qs.DataSource` subclasses will all provide a common interface (the one
defined in `wmc.qs.DataSource`, with the core purpose of producing timeseries
data for metrics and events. A metric is something that can be sampled at a
particular time with instantaneous duration (heart rate, blood pressure, gps
location, etc). An event is something that happens at a specific time and may
(or may not) have a duration (watching a youtube video, purchasing something
from amazon, a financial transaction, visiting a url in Chrome, switching
buffers in Emacs, sending an email, receiving an email, etc).

The `wmc.qs.MetricSeries` class efficiently maintains timeseries information
for a metric.  The `wmc.qs.Event` and `wmc.qs.EventSeries` classes maintain
timeseries information for a specific Event. The `wmc.qs.Stream` class is
an abstract superclass of ``wmc.qs.MetricSeries` and `wmc.qs.EventSeries`
(and possibly other classes) that represents some quantifiable, measurable
piece of data about me. The `wmc.qs.Env` class maintains all data sources,
all streams, and functionality for convering data sources to streams in an
efficient and persistent and canonicalized manner.

One of the core sources of data will be Google Takeout
(https://takeout.google.com). The following will use Google Takeout as an
example of some of the complexity that Meta<Self> needs to navigate when
converting data sources to canonicalized streams.

Google Takeout allows one to acquire a great deal of information about one's
use of numerous Google services and products. One requests data from
https://takeout.google.com, which can be downloaded into .zip or .tgz files
which when extracted always produces a Takeout directory, with one or more
subdirectories depending on which services/products were selected during the
takeout process.

For example:
 - every url one has ever visited is captured in Takeout/Chrome/History.json
   (but there are numerous other files present for Chrome as well, including
   Takeout/Chrome/{Extensions,Addresses and more,Settings,OS Settings,Device
   Information}.json, Takeout/Chrome/{Bookmarks,Reading List}.html, and
   Takeout/Chrome/Dictionary.csv). This highlights that input streams come in
   many different formats. Furthermore, the exact format of individual files
   can change over time (so our DataSource subclasses need to have the concept
   of per-file versions dictated by date ranges, and the ability to handle
   various file versions/formats)
 - every email sent or received is captured in
   All\ mail\ Including\ Spam\ and\ Trash-002.mbox (unfortunately NOT placed
   in Takeout/Mail be default, although our extraction process should probably
   do this). Note that there is a Takeout/Mail/UserSettings directory with
   files Filters.json, Delegated Sender Addresses.json, and Forwarding Address.json.
 - every Youtube video watched is
   captured in `Takeout/YouTube and YouTube Music/history/watch-history.html`
   (but there is also Youtube-specific data in
   `Takeout/My\ Activity/YouTube/MyActivity.html`, which highlights that
   source-specific data can be scattered across multiple directories within
   the Takeout directory ... our parsers will need to handle this).

I mentioned above that the formats of files can change over time. Our parsers
will need to be very careful not to make assumptions about format that would
break the code (assumptions must be tested, and the code must report situations
where assumptions are violated, as this usually implies we are looking at a
data format change that needs to be accounted for).

Another important aspect is that Takeout data is associated with a specific
google account (aka email address). People often have multiple google email
addresses, and it is the sum of all data across all such accounts that is
relevant. Our code must be able to parse takeout data from multiple accounts and
merge them into data for a Person (while also maintaining the "persona" (aka
email address) the data was associated with). A `wmc.qs.Person` captures
all data across multiple `wmc.qs.Persona` instances. It is important to
maintain a distinction between Person and Persona.

The data provided in Takeout directories is NOT a complete history of data.
It only represents data for a specific (source-specific) amount of time, within
some data sources purging older data regularly. This means that each Takeout
directory must be treated as a subset of the complete history of all data, and
introduces specific implementation challenges and decision points.

One big architectural question still to be resolved is whether we maintain a
"universal" Takeout directory, and write code to merge partial Takeout
directories into this "universal" directory, or do we go directly from partial
Takeout directories into our final canonicalized representation.

The former approach gives us a clean representation of all input data from
which we can recreate canonical output any time. However, it has cons too:

   - introduces complexities around merging files from partial Takeouts into
     files in the universal Takeout directory files since the partial files
     may not represent all data ... we need to do PER-FILE merging, not just
     blindly copy files from one Takeout directory to another
   - requires double or more the disk space as the other approach

The latter approach addresses both cons of the former approach, but has a big
negative as well:
 - we do not have a canonical source of input data, and thus cannot recreate
   the canonical source at any time. If we make mistakes inserting data during
   the partial Takeout merging process, we have no clean way of undoing them

- Record *everything* possible about myself

   - Use the concept of time-series data streams
      - each stream represents a certain kind of information
         - emails
         - chats
         - fitbit heart rate
         - CGM glucose readings
      - each stream has various concepts
         - raw input data (for a specific date range): e.g. google takeout, fitbit data format, etc
         - canonicalized time-stream data

   - Google Takeout:
      - streams: emails, chats, photos, log activity, calendar, chrome history,
        contacts, drive metadata and data, google fit, gemini, google fi phone
        calls, google finance, google meet, google one, google pay, google
        books, google movies/tv, google play, google store, google wallet,
        groups, home app, keep, maps, activity, nest, notebook, audio
        recordings, saved, tasks, timeline, voice, youtubue
      - features
         - Individual .zip or .tgz files downloaded from takeout.google.com
           must be integrated into a "universal" directory hierarchy
            - cannot just unzip into that universal directory, because takeout
              sometimes prunes data (at inter-file and intra-file levels), so
              file `somefile.json` within the universal directory may
              contain data from date W to Y, but the same file within a
              Takeout dir is from date X to Z (W < X < Y < Z). We need to
              perform per-takeout-file record extraction into a canonical
              date-specific format
            - once a takeout file has been added to the universal directory
              structure, it can be deleted (which means we need to extract
              ALL data)

   - location data
      - weather, barometric pressure, etc

   - fitbit/pixel watch/etc
      - heart rate
      - variability
      - exercises/activity
      - what else?

   - food
      - scan receipts
      - link to USDA for nutritional details
      - weigh foods

   - labs/tests
      - weight
      - blood pressure and O2
      - urine strips
      - blood work
      - CGM (and other upcoming devices)

- Parse Google Takeout data
   - https://github.com/purarue/google_takeout_parser/blob/master/README.md

- NiaHealth (membership paused until 2027-07-26 ($2400 CAD)
   - https://app.niahealth.co/profile/account/manage-plan
   - look at dashboard, acquire all data
   - cancel membership (or decide if it is a good replacement for GP)

- Fountain Life
   - https://app.us.fountainlife.com/

- Dexcom
   - https://account.dexcom.com/en-ca/profiles

- Google Fit?

- Alberta MyHealth

- Dexcom
   - https://clarity.dexcom.eu/i/#/agp
   - https://account.dexcom.com/en-ca

## Meta<Account>: Integrated website/account management

- Maintain a comprehensive list of EVERY website account
   - how to login (email, username, password, 2FA, etc)
   - scope of website (what issues does this website solve?)
      - create vectors in OpenClaw so it can identify which website can solve
        a specific problem (e.g. renew vehicle registration, see my prescriptions, buy an item, etc)
   - how to change password and 2FA settings
   - how to close account
   - how to delete account

- List
   - Albera eServices: https://eservices.alberta.ca/
   - Alberta.ca:       https://account.alberta.ca/
   - MyHealth:         https://myhealth.alberta.ca/

   - Dexcom
      - Data: https://clarity.dexcom.eu/i/#/overview
      - Admin: https://account.dexcom.com/en-CA

## Meta<Comms>: Integrated Communication Channels

- I have one or more accounts on every single communication channel
  (Email, Discord, Slack, Telegram, SMS, etc)
   - an OpenClaw agent is assigned to monitor almost all streams, and to
     transfer messages from those streams to a central hub, where I can
     view and respond to those messages
   - when I send a response, it gets delivered via the appropriate channel
     and account to that person's preferred communication channel

## Meta<Social>: Integrated Social Networking

- The same kind of integration can happen for social media (facebook, instagram,
  bluesky, twitter, etc)
   - I have an account on all social media sites
   - An personal AI agent is assigned to each site, and monitors DMs to me,
     as well as general posts from others
   - Allows my agents to build up a knowledge base for every friend/acquitance
     based on their social media presence

## Meta<Finance>: Track Everything Financial

- parse bank/cc/investment statements to identify transactions
- algorithmically/heuristically/LLmily establish category/subcategory for
  every transaction
- distribute transactions across day ranges
- visualize per day, per week, per month and per year break downs of
  transactions
- produce reports useful for taxes each year

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

- Power down and get UPS installed
   - won't have Kasa HP300 #2 until October
   - plug following into Kasa (which goes into UPS)
      - 0: Shaw Router
      - 1: spark1
      - 2: spark2
      - 3: evo-x2
      - 4: k8 plus
      - 5: binardat switch

- Get DGX Spark #1 set up and integrated into MetaClaw
- Get DGX Spark #2 set up and linked/chained with DGX Spark #1

- Start working on Meta<Self>

- Get bin/power_kasa.py updated to support devices moving from port to
  port. Also support acquisition of power readings every N minutes or seconds
  and log this someplace

- Get browser provider implemented and working
   - want to be able to extract core text from amazon listings, youtube videos,
     wikipedia entries, etc.

- Get pdf parsing working so we can move forward on Meta<Finance>

- Close wellsfargo accounts?
- Cancel Canada Amazon Prime before 2026-09-25
- Look into amazon pharmacy


