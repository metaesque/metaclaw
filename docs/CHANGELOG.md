# MetaClaw Changelog

This document records significant changes and updates made to the MetaClaw framework.

## 2026-06-27

* **Release `stable-v1`**: Successfully achieved a stable, working Tier 0 OpenClaw
  environment.
* **Open Source Repository**: Officially established the public MetaClaw repository
  at [https://github.com/metaesque/metaclaw](https://github.com/metaesque/metaclaw).
* **Housekeeping**: Removed all auto-generated `services/**/index.md` files from
  version control to prevent merge conflicts. These files are now generated locally
  via the `make docs` or `make wizard` pipeline.

## 2026-06-20

* **Milestone Achieved**: Successfully transitioned MetaClaw framework development
  out of external browser-based LLM chats (e.g., gemini.google.com) and moved it
  natively into the user's local OpenClaw deployment. The OpenClaw software agent
  now has read/write access to the MetaClaw repository via a mounted workspace and
  can actively develop the framework.
