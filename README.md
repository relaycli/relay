<p align="center">
  <a href="https://relaycli.com"><img src="https://zugjkckdxhiamdlkxfmv.supabase.co/storage/v1/object/public/assets//logo_light.svg" width="75" height="75"></a>
</p>
<h1 align="center">
 Relay - protocol-native CLI for email management
</h1>
<p align="center">
  <a href="https://github.com/relaycli/relay">CLI</a> ・
  <a href="https://discord.gg/T4zbT7RcVy">Discord</a> ・
  <a href="https://docs.relaycli.com">Documentation</a>
</p>
<h2 align="center"></h2>

<p align="center">
  <a href="https://github.com/relaycli/relay/actions?query=workflow%3Acore">
    <img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/relaycli/relay/core.yml?branch=main&label=CI&logo=github&style=flat-square">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/badge/Linter-Ruff-FCC21B?style=flat-square&logo=ruff&logoColor=white" alt="ruff">
  </a>
  <a href="https://github.com/astral-sh/ty">
    <img src="https://img.shields.io/badge/Typecheck-Ty-261230?style=flat-square&logo=astral&logoColor=white" alt="ty">
  </a>
  <a href="https://codecov.io/gh/relaycli/relay">
    <img src="https://img.shields.io/codecov/c/github/relaycli/relay.svg?logo=codecov&style=flat-square&token=48QKJKDCYP" alt="Test coverage percentage">
  </a>
</p>
<p align="center">
  <a href="https://pypi.org/project/relaycli/">
    <img src="https://img.shields.io/pypi/v/relaycli.svg?logo=PyPI&logoColor=fff&style=flat-square&label=PyPI" alt="PyPi Version">
  </a>
  <img alt="GitHub release (latest by date)" src="https://img.shields.io/github/v/release/relaycli/relay?label=Release&logo=github">
  <a href="https://github.com/relaycli/relay/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/relaycli/relay.svg?label=License&logoColor=fff&style=flat-square" alt="License">
  </a>
</p>
<p align="center">
  <a href="https://discord.gg/T4zbT7RcVy">
    <img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat-square&logo=discord&logoColor=white" alt="Discord">
  </a>
  <a href="https://twitter.com/relaycli">
    <img src="https://img.shields.io/badge/Twitter-@relaycli-1D9BF0?style=flat-square&logo=twitter&logoColor=white" alt="Twitter">
  </a>
</p>

Relay helps builds create apps on email workflows. See it as a crossover between an email client and Claude code ✉️


## Quick Tour

### Fetching your unread emails

```shell
relay messages ls --limit 10 --unread
```
```
Using account: piedpiper
                            Messages from richard@piedpiper.com
┏━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ UID   ┃ Timestamp                ┃ From                          ┃ Subject    ┃ Snippet    ┃
┡━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 15443 │ 2025-06-23 12:35:44 UTC  │ gilfoyle@piedpiper.com        │ Server     │ The        │
│       │                          │                               │ migration  │ migration  │
│       │                          │                               │ complete   │ is done... │
│ 15467 │ 2025-06-26 12:46:09 UTC  │ dinesh@piedpiper.com          │ RE: My     │ Actually   │
│       │                          │                               │ code is    │ Gilfoyle,  │
│       │                          │                               │ perfect    │ your cod...│
│ 15555 │ 2025-07-08 15:46:27 UTC  │ jared@piedpiper.com           │ Team       │ Hi guys!   │
│       │                          │                               │ building   │ I've       │
│       │                          │                               │ retreat    │ organized..│
│ 15587 │ 2025-07-10 13:34:48 UTC  │ monica@raviga.com             │ Q3         │ Richard,   │
│       │                          │                               │ metrics    │ we need to │
│       │                          │                               │ review     │ discuss... │
│ 15588 │ 2025-07-10 14:22:49 UTC  │ gavin@hooli.com               │ Acquisition│ Pied Piper │
│       │                          │                               │ offer      │ team, I'm  │
│       │                          │                               │            │ prepared...│
└───────┴──────────────────────────┴───────────────────────────────┴────────────┴────────────┘
Showing 5 of 5 unread messages
```

### Reading email details

```shell
relay messages cat 15443
```
```
Using account: piedpiper

Message Details
UID: 15443
Timestamp: 2025-06-23 12:35:44 UTC
Subject: Server migration complete
From: "Bertram Gilfoyle" <gilfoyle@piedpiper.com>
To: richard@piedpiper.com
CC: dinesh@piedpiper.com, jared@piedpiper.com
BCC: N/A

Message Body:
The migration is done. Obviously.

While you were all probably panicking about downtime (which never happened),
I successfully migrated our entire server infrastructure to the new data center.

Key accomplishments:
- Migrated 47 servers in 3.2 hours
- Implemented redundant failsafes
- Optimized database queries by 340%
- Fixed 23 security vulnerabilities

Richard, the system is now running at 99.97% efficiency. The remaining 0.03%
is due to the laws of physics, which even I cannot override.

Dinesh, I've documented everything in a way that even you might comprehend,
though I make no guarantees.

The servers are purring like a well-fed cat. You may now return to your
regularly scheduled mediocrity.

--
Bertram Gilfoyle
Senior Systems Architect
Pied Piper Inc.

No attachments
```


## Get started 🚀

### Prerequisites

- [UV](https://docs.astral.sh/uv/getting-started/installation/)

### 30 seconds setup ⏱️ ([docs](https://docs.relaycli.com/documentation/getting-started/quickstart))

#### 1 - Install the CLI
```shell
pip install relaycli
```
#### 2 - Connect your email account
```shell
relay accounts add
```
Follow the instructions to connect your email account.

#### 3 - Play with the CLI

```shell
relay messages --help
```
```
 Usage: relay messages [OPTIONS] COMMAND [ARGS]...

 Email message commands


╭─ Options ──────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────╮
│ list | ls              List recent emails from specified account.                          │
│ open | cat             Read a single email message by UID.                                 │
│ search | find | grep   Search for messages containing the specified query.                 │
│ trash | rm             Move a message to trash.                                            │
│ spam                   Mark a message as spam.                                             │
│ mark                   Mark a message as read or unread.                                   │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Contributing

Oh hello there 👋 If you've scrolled this far, we bet it's because you like open-source. Do you feel like integrating a new email provider? Or perhaps improve our documentation? Or contributing in any other way?

You're in luck! You'll find everything you need in our [contributing guide](CONTRIBUTING.md) to help grow this project! And if you're interested, you can join us on [Discord](https://discord.gg/T4zbT7RcVy) 🤗


## Copying & distribution

Copyright (C) 2025, Relay.

This program is licensed under the Apache License 2.0.
See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Frelaycli%2Frelay.svg?type=large&issueType=license)](https://app.fossa.com/projects/git%2Bgithub.com%2Frelaycli%2Frelay?ref=badge_large&issueType=license)
