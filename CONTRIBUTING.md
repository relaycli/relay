# Contributing to Relay ✉️

Welcome 🤗
The resources compiled here are meant to help developers contribute to the project. Please check the [code of conduct](CODE_OF_CONDUCT.md) before going further.

If you're looking for ways to contribute, here are some ideas:
- 🐛 Report bugs (open an [issue](https://github.com/relaycli/relay/issues/new?labels=type%3A+bug&template=bug_report.yml) & fill the template)
- 💡 Suggest improvements (open a [GitHub discussion](https://github.com/relaycli/relay/discussions/new?category=ideas) or chat with us on [Discord](https://discord.gg/T4zbT7RcVy))
- 👍👎 Provide feedback about our [roadmap](https://docs.relaycli.com/community/roadmap) (easier to chat on [Discord](https://discord.gg/T4zbT7RcVy))
- ⌨️ Update the codebase (check our guide for [setup](#developer-setup) & [PR submission](#submitting-a-pull-request))


## High-level products

### Python SDK

Protocol-native client for email interactions

### CLI

Command line interface for the SDK


## Codebase structure

- [`./relay`](https://github.com/relaycli/relay/blob/main/relay) - The actual API codebase
- [`./cli`](https://github.com/relaycli/relay/blob/main/cli) - The API unit tests
- [`.github`](https://github.com/relaycli/relay/blob/main/.github) - Configuration for CI (GitHub Workflows)
- [`./docs`](https://github.com/relaycli/relay/blob/main/docs) - Source of our documentation


## Continuous Integration

This project uses the following integrations to ensure proper codebase maintenance:

- [Github Worklow](https://help.github.com/en/actions/configuring-and-managing-workflows/configuring-a-workflow) - run jobs for package build and coverage
- [Codecov](https://codecov.io/) - reports back coverage results
- [Mintlify](https://mintlify.com/) - the documentation builder

As a contributor, you will only have to ensure coverage of your code by adding appropriate unit testing of your code.



## Feedback

### Feature requests & bug report

Whether you encountered a problem, or you have a feature suggestion, your input has value and can be used by contributors to reference it in their developments. For this purpose, we advise you to use Github [issues](https://github.com/relaycli/relay/issues).

First, check whether the topic wasn't already covered in an open / closed issue. If not, feel free to open a new one! When doing so, use issue templates whenever possible and provide enough information for other contributors to jump in.

### Questions

If you are wondering how to do something with Relay, or a more general question, you should consider checking out Github [discussions](https://github.com/relaycli/relay/discussions). See it as a Q&A forum, or the project-specific StackOverflow!


## Developer setup

### Prerequisites

- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [UV](https://docs.astral.sh/uv/getting-started/installation/)
- [Make](https://www.gnu.org/software/make/) (optional)


### Configure your fork

1 - Fork this [repository](https://github.com/relaycli/relay) by clicking on the "Fork" button at the top right of the page. This will create a copy of the project under your GitHub account (cf. [Fork a repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo)).

2 - [Clone your fork](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) to your local disk and set the upstream to this repo
```shell
git clone git@github.com:<YOUR_GITHUB_ACCOUNT>/relay.git
cd relay
git remote add upstream https://github.com/relaycli/relay.git
```

### Install the dependencies

Let's install the different libraries:
```shell
make install-cli
```

#### Pre-commit hooks
Let's make your life easier by formatting & fixing lint on each commit:
```shell
pre-commit install
```

## Submitting a Pull Request

### Preparing your local branch

You should not work on the `main` branch, so let's create a new one
```shell
git checkout -b a-short-description
```

### Developing your feature

#### Commits

- **Code**: ensure to provide docstrings to your Python code. In doing so, please follow [Google-style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) so it can ease the process of documentation later.
- **Commit message**: please follow [Angular commit format](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#-commit-message-format)

#### Tests

In order to run the same tests as the CI workflows, you can run them locally:

```shell
make test
```

#### Code quality

To run all quality checks together

```shell
make quality
```

The previous command won't modify anything in your codebase. Some fixes (import ordering and code formatting) can be done automatically using the following command:

```shell
make style
```

### Submit your modifications

Push your last modifications to your remote branch
```shell
git push -u origin a-short-description
```

Then [open a Pull Request](https://docs.github.com/en/github/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) from your fork's branch. Follow the instructions of the Pull Request template and then click on "Create a pull request".
