<p align="center">
  <a href="https://relaycli.com"><img src="https://zugjkckdxhiamdlkxfmv.supabase.co/storage/v1/object/public/assets//logo_light.svg" width="75" height="75"></a>
</p>
<h1 align="center">
 Relay - Claude Code meets Gmail API
</h1>
<p align="center">
  <a href="https://github.com/relaycli/relay">CLI</a> ・
  <a href="https://discord.gg/T4zbT7RcVy">Discord</a> ・
  <a href="https://docs.relaycli.com">Documentation</a>
</p>
<h2 align="center"></h2>

<p align="center">
  <a href="https://github.com/relaycli/relay/actions?query=workflow%3Aengine">
    <img alt="CI Status" src="https://img.shields.io/github/actions/workflow/status/relaycli/relay/engine.yml?branch=main&label=CI&logo=github&style=flat-square">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/badge/Linter-Ruff-FCC21B?style=flat-square&logo=ruff&logoColor=white" alt="ruff">
  </a>
  <a href="https://github.com/astral-sh/ty">
    <img src="https://img.shields.io/badge/Typecheck-Ty-261230?style=flat-square&logo=astral&logoColor=white" alt="ruff">
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
    <img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat-square&logo=discord&logoColor=white" />
  </a>
  <a href="https://twitter.com/relaycli">
    <img src="https://img.shields.io/badge/-@relaycli-1D9BF0?style=flat-square&logo=twitter&logoColor=white" alt="Twitter">
  </a>
</p>

Relay helps builds create apps on email workflows. See it as a crossover between an email client and Claude code ✉️


## Quick Tour

### Fetching your emails

```shell
relay messages ls
```
That's it!


## Get started 🚀

### Prerequisites

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [UV](https://docs.astral.sh/uv/getting-started/installation/)
- [Make](https://www.gnu.org/software/make/) (optional)

### 30 seconds setup ⏱️

#### 1 - Install the CLI
```shell
uv pip install --system relaycli
```
#### 2 - Connect your email account
```shell
relay account add
```
Follow the instructions to connect your email account.

#### 3 - Play with the CLI

```shell
relay messages ls
```

## Contributing

Oh hello there 👋 If you've scrolled this far, we bet it's because you like open-source. Do you feel like integrating a new email provider? Or perhaps improve our documentation? Or contributing in any other way?

You're in luck! You'll find everything you need in our [contributing guide](CONTRIBUTING.md) to help grow this project! And if you're interested, you can join us on [Discord](https://discord.gg/T4zbT7RcVy) 🤗


## Copying & distribution

Copyright (C) 2025, Relay.

This program is licensed under the Apache License 2.0.
See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Frelaycli%2Frelay.svg?type=large&issueType=license)](https://app.fossa.com/projects/git%2Bgithub.com%2Frelaycli%2Frelay?ref=badge_large&issueType=license)
