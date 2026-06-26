# lavague: LaVague

## Overview

Instead of just acting as a simple browser, LaVague utilizes a 'World Model' to
understand the visual state of a webpage and an 'Action Engine' to compile that
understanding into standard automation scripts (like Selenium or Playwright). It
effectively acts as an autonomous QA engineer that writes its own code on the
fly to achieve an objective.

For OpenClaw, LaVague serves as an advanced cognitive translation layer. If you
ask OpenClaw to 'Download the latest invoice from AWS', LaVague handles the
complex reasoning of mapping the AWS interface into a series of actionable code
steps.

Furthermore, because LaVague outputs standard automation code, OpenClaw can save
that generated script locally. This allows the framework to execute the exact
same task later with zero AI overhead, permanently expanding OpenClaw's library
of rigid, reliable skills.
