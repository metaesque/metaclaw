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

- Record *everything* possible about myself

   - Google Takeout for emails, chats, photos, log activity, calendar, chrome
     history, contacts, drive metadata and data, google fit, gemini, google fi
     phone calls, google finance, google meet, google one, google pay, google
     books, google movies/tv, google play, google store, google wallet, groups,
     home app, keep, maps, activity, nest, notebook, audio recordings, saved,
     tasks, timeline, voice, youtubue

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

## Meta<Health>: Integrated Health

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

## TODOs

- Acquire power cord
- Get DGX Spark #1 set up and integrated into MetaClaw
- Get DGX Spark #2 set up and linked/chained with DGX Spark #1

- Close wellsfargo accounts?
- Cancel Canada Amazon Prime before 2026-09-25
- Look into amazon pharmacy


