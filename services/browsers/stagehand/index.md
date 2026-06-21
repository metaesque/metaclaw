# stagehand: Stagehand

## Overview

The fundamental problem with pure AI web browsing is that it can be
unpredictable and expensive, consuming thousands of tokens to figure out how to
click a simple 'Next' button. Stagehand solves this by allowing OpenClaw to use
rigid, instantaneous code for the parts of a website that never change, while
selectively calling on an AI model to navigate confusing or dynamic sections.

Specifically for OpenClaw, Stagehand introduces the ability to 'cache' actions.
Once the AI successfully figures out how to navigate a complex login screen,
Stagehand remembers the exact steps.

The next time OpenClaw runs that task, it bypasses the expensive AI evaluation
step and executes the cached code instantly, resulting in massive API cost
savings and vastly improved reliability for your daily background tasks.
