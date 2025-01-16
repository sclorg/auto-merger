## auto-merger

The auto-merger is tool for analysis pull request and provide feedback maintainers
what is missing in each pull request. User can specify in `.automerger.yaml` configuration file
what labels block the pull request for merging.

The auto-merger does not count pull request that are marked as `Draft`

The auto-merger provides two options, that are described below.

Before running `auto-merger` you have to export GH_TOKEN, that is mandatory for command `gh` that
is used for work in GitHub.

# Configuration file

The configuration file should be present in `$HOME` directory where the automerger is running.

The full example configuration file looks like:

```yaml
github:
  namespace: "sclorg"
  repos:
    - valkey-container
  # How many approvals should have PR - default is 2
  approvals: 2
  # How many days, PR should be opened - default is 1 day
  pr_lifetime: 1
  # Labels that blockes merges
  blocker_labels:
    - "pr/failing-ci"
    - "pr/missing-review"
  # Labels that should be present in pull request before merging
  approval_labels:
    - "READY-to-MERGE"
```
where keys mean:
* `github` - specifies everything related to https://github.com/ pull request.
* `namespace` - specifies `namespace` in https://github.com where the pull requests will be analysed
* `repos` - specifies repositories that will be used for analysis
* `approvals` - how many approvals do you need before merging. Default is `2`
* `pr_lifetime` - how many `days` corresponding pull request should be opened. Default is `1`
* `blocker_labels` - specifies GitHub labels, that blocks pull request against merging
* `approval_labels` - specifies GitHub labels, that allows pull request merging

# Pull Request checker

This option is used for analysation pull request in the specific namespace and repositories mentioned
in configuration file. At the end `auto-merger` provides the output into command line.

```bash
$ auto-merger pr-checker --help
Usage: auto-merger pr-checker [OPTIONS]

Options:
  --send-email TEXT  Specify email addresses to which the mail will be sent.
  --help             Show this message and exit.

```

The real output from `auto-merger pr-checker` could be:
```bash
s2i-ruby-container
------

https://github.com/sclorg/s2i-ruby-container/pull/570 pr/missing-review pr/failing-ci
https://github.com/sclorg/s2i-ruby-container/pull/569 dependencies ruby pr/missing-review

s2i-nodejs-container
------

https://github.com/sclorg/s2i-nodejs-container/pull/463 pr/missing-review pr/failing-ci
https://github.com/sclorg/s2i-nodejs-container/pull/236 pr/missing-review


Pull requests that can be merged or missing 2 approvals
https://github.com/sclorg/s2i-python-container/pull/574 - Missing 2 APPROVAL
```

In case user specifies `--send-email`, multipletimes, and the system where is auto-merger running
the email service is configured, then the results are send to corresponding emails.

# Automatic pull request merger

This option is used for analysation pull request in the specific namespace and repositories mentioned
in configuration file. At the end `auto-merger` provides the output into command line.

```bash
$ auto-merger pr-checker --help
Usage: auto-merger pr-checker [OPTIONS]

Options:
  --send-email TEXT  Specify email addresses to which the mail will be sent.
  --help             Show this message and exit.

```

The real output from `auto-merger pr-checker` could be:
```bash
s2i-ruby-container
------

https://github.com/sclorg/s2i-ruby-container/pull/570 pr/missing-review pr/failing-ci
https://github.com/sclorg/s2i-ruby-container/pull/569 dependencies ruby pr/missing-review

s2i-nodejs-container
------

https://github.com/sclorg/s2i-nodejs-container/pull/463 pr/missing-review pr/failing-ci
https://github.com/sclorg/s2i-nodejs-container/pull/236 pr/missing-review


Pull requests that can be merged or missing 2 approvals
https://github.com/sclorg/s2i-python-container/pull/574 - Missing 2 APPROVAL
```

In case user specifies `--send-email`, multipletimes, and the system where is auto-merger running
the email service is configured, then the results are send to corresponding emails.
