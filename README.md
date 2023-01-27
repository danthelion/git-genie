# git-genie

Generate & explain git commands using plain english.

## Installation

```bash
pip install git-genie
```

## Usage

`❯ git-genie [OPTIONS] INSTRUCTION`

Options:
 - --explain, -e: Explain the generated git command automatically.
 - --execute, -x: Execute the generated git command automatically.
 - --install-completion: Install completion for the current shell.
 - --show-completion: Show completion for the current shell, to copy it or customize the installation.
 - --help, -h: Show this message and exit.

If no options are provided, the program will run in interactive mode.

Optionally, you can add a "gg" alias to your shell's rc file (e.g. ~/.bashrc) to make the command shorter:

```bash
alias gg="git-genie"
```

### Pre-requisites

#### OpenAI API key

```shell
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Interactive mode

```bash
~/git-genie ❯ git-genie "count how many times the README.md file was modified in the last week"

Generated git command: git log --since=1.week -- README.md | grep "^commit" | wc -l

(E)xplain or e(X)ecute or (N)ew?: E

Explanation
 git log -> Show commit logs
--since=1.week -> Show commits more recent than a specific date
-- README.md -> Only commits that affect README.md
| -> Pipe the output of the previous command to the next command
grep "^commit" -> Only show lines that start with "commit"
wc -l -> Count the number of lines

e(X)ecute or (N)ew?: X

Running command:  git log --since=1.week -- README.md | grep "^commit" | wc -l
Output:
       2
```

### Non-interactive mode

#### Explain

```bash
~/git-genie ❯ git-genie "amend all previous commits with new email address" --explain

Generated git command:  git rebase -i HEAD~5 --autosquash -m "legacy code"

Explanation

 git rebase -> Forward-port local commits to the updated upstream head
-i, --interactive -> Make a list of the commits which are about to be rebased.Let the user edit that list before rebasing.
--autosquash -> Automatically move commits that begin with squash!/fixup! to the beginningof the todo list.
-m, --merge -> Use the given message as the merge commit message.If multiple -m options are given, their values are concatenated as separate paragraphs.
HEAD~5 -> The last 5 commits
legacy code -> The message of the merge commit
```

#### Execute

```bash
~/git-genie ❯ git-genie "print last 5 commits logs, condensed" --execute

Generated git command:  git log -5 --oneline

Running command:  git log -5 --oneline

Output:
9a33bc3 update email
f76f041 CLI interface
ae8abbd Add pycache to gitignore
67169fd rich print
3bac238 Refactor
```
