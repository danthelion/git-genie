import argparse
import subprocess

import typer
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from rich import print

DEBUG_MODE = False
QUIET_MODE = False

LLM = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-1106")

COMMS_COLOR = "yellow"
COMMAND_COLOR = "bold red"
EXPLANATION_COLOR = "bold green"

GENERATE_GIT_COMMAND_EXAMPLES = [
    {"instruction": "Revert last 3 commits", "command": "git reset --hard HEAD~3"},
    {"instruction": "list all branches", "command": "git branch"},
    {
        "instruction": "Create a new branch called 'feature'",
        "command": "git checkout -b feature",
    },
    {
        "instruction": "Switch to the 'feature' branch",
        "command": "git checkout feature",
    },
    {
        "instruction": "Create a new branch called 'feature' and switch to it",
        "command": "git checkout -b feature",
    },
    {
        "instruction": "Merge the 'feature' branch into the 'master' branch",
        "command": "git checkout master && git merge feature",
    },
    {
        "instruction": "Merge the 'feature' branch into the 'master' branch, but don't create a merge commit",
        "command": "git checkout master && git merge --no-ff feature",
    },
    {
        "instruction": "Rebase the last 5 commits onto the 'master' branch, but don't create a merge commit",
        "command": "git rebase -i HEAD~5 --autosquash -m 'legacy code'",
    },
]

EXPLAIN_GIT_COMMAND_EXAMPLES = [
    {
        "command": 'git rebase -i HEAD~5 --autosquash -m "legacy code"',
        "explanation": "git rebase -> Forward-port local commits to the updated upstream head\n"
        "-i, --interactive -> Make a list of the commits which are about to be rebased."
        "Let the user edit that list before rebasing.\n --autosquash ->"
        "Automatically move commits that begin with squash!/fixup! to the beginning"
        "of the todo list.\n -m, --merge -> Use the given message as the merge commit message."
        "If multiple -m options are given, their values are concatenated as separate paragraphs."
        "\nHEAD~5 -> The last 5 commits\nlegacy code -> The message of the merge commit",
    },
    {
        "command": "git push origin master --force-with-lease",
        "explanation": "git push -> Update remote refs along with associated objects\norigin ->"
        "The remote repository\nmaster -> The branch to push\n--force-with-lease ->"
        "If the remote branch is not an ancestor of the local branch, refuse to push."
        "This can be used to prevent the remote branch from being overwritten.",
    },
    {
        "command": "git log --since=1.week --name-only --oneline -- test.json | grep test.json | wc -l",
        "explanation": "git log -> Show commit logs\n--since=1.week -> Show commits more recent than a"
        "specific date\n--name-only -> Show only names of changed files\n--oneline ->"
        "Show only the first line of each commit message\n-- test.json -> Only commits that"
        "affect test.json\n| -> Pipe the output of the previous command to the next command\ngrep"
        "test.json -> Only show lines that contain test.json\nwc -l -> Count the number of lines",
    },
    {
        "command": "git log --graph --decorate --oneline --all -n 5",
        "explanation": "git log -> Show commit logs\n--graph -> Show an ASCII graph of the branch and merge"
        "history beside the log output\n--decorate -> Show the ref names of any commits that are"
        "shown\n--oneline -> Show only the first line of each commit message\n--all ->"
        "Show all commits, including those that are not reachable from any branch\n-n 5 ->"
        "Show only the last 5 commits",
    },
]

app = typer.Typer()


def quiet_print(text: str):
    if not QUIET_MODE:
        print(text)


def generate_git_command(instruction: str):
    example_formatter_template = """
    You are an interpreter for the command line version control tool git. Translate the following human-readable
    instructions into git commands. You can use the following examples as a reference. Only return commands that are
    syntactically correct and produce the desired effect. If you don't know how to translate an instruction, return
    'git help'.

    Instructon: {instruction}
    Command: {command}\n
    """
    example_prompt = PromptTemplate(
        input_variables=["instruction", "command"],
        template=example_formatter_template,
    )

    few_shot_prompt = FewShotPromptTemplate(
        examples=GENERATE_GIT_COMMAND_EXAMPLES,
        example_prompt=example_prompt,
        prefix="Translate the following human-readable instructions into git commands.",
        suffix="Human-readable instruction: {input}\nGit command:",
        input_variables=["input"],
        example_separator="\n\n",
    )

    git_command_translator = LLMChain(llm=LLM, prompt=few_shot_prompt)
    git_command = git_command_translator(instruction)["text"]
    quiet_print(
        f"[{COMMS_COLOR}]Generated git command:[/{COMMS_COLOR}] [{COMMAND_COLOR}]{git_command}[/{COMMAND_COLOR}]"
    )
    return git_command


def explain_git_command(git_command: str):
    explain_example_formatter_template = """
    Give a detailed explanation of the following git command. Explain each part of the command separately, similar to
    how it would be explained in a unix man page.

    Command: {command}
    Explanation: {explanation}\n
    """
    explain_example_prompt = PromptTemplate(
        input_variables=["command", "explanation"],
        template=explain_example_formatter_template,
    )

    explain_few_shot_prompt = FewShotPromptTemplate(
        examples=EXPLAIN_GIT_COMMAND_EXAMPLES,
        example_prompt=explain_example_prompt,
        prefix="Explain the followng git command.",
        suffix="Git command: {input}\nExplanation:",
        input_variables=["input"],
    )

    git_command_translator = LLMChain(llm=LLM, prompt=explain_few_shot_prompt)
    explanation = git_command_translator(git_command)["text"]
    quiet_print(f"[{COMMS_COLOR}]Explanation[/{COMMS_COLOR}]\n[{EXPLANATION_COLOR}]{explanation}[/{EXPLANATION_COLOR}]")
    return explanation


def execute_git_command(git_command: str):
    quiet_print(f"[{COMMS_COLOR}]Running command:[/{COMMS_COLOR}] [{COMMAND_COLOR}]{git_command}[/{COMMAND_COLOR}]")
    result = subprocess.run(git_command, shell=True, capture_output=True, text=True)
    quiet_print(f"[{COMMS_COLOR}]Output:[/{COMMS_COLOR}]")
    if result.stdout:
        typer.echo(result.stdout)
    if result.stderr:
        typer.echo(result.stderr)
    exit(0)


def get_diff():
    # Get diff of current state
    get_diff_cmd = "git diff --staged"
    result = subprocess.run(get_diff_cmd, shell=True, capture_output=True, text=True)
    diff = result.stdout
    # check if there are any changes
    if not diff:
        quiet_print(f"[{COMMS_COLOR}]No changes detected. Stage files with `git add` first.[/{COMMS_COLOR}]")
        exit(0)
    return diff


def generate_commit_message(diff: str) -> str:
    text_splitter = CharacterTextSplitter(separator="\n")
    texts = text_splitter.split_text(diff)
    docs = [Document(page_content=t) for t in texts]

    # summarize changes first
    summary_chain = load_summarize_chain(LLM, chain_type="stuff")
    changes_summary = Document(page_content=summary_chain.run(docs))

    prompt_template = """
    You are a version control system. Generate a commit message for the following changes. The commit message should be
    a short description of the changes. The commit message should be written in the imperative mood, i.e. as if you were
    giving a command. The first line should be no longer than 50 characters and should start with a capital letter. The
    following lines should be no longer than 72 characters.

    Only focus on the changed lines. Do not include lines that were not changed.

    Be direct, try to eliminate filler words and phrases in these sentences (examples: though, maybe, I think, kind of).
    Think like a journalist. Be concise. Be clear. Be consistent. Be professional. Be respectful.

    Changes: {text}

    Commit message:"""
    summary_prompt_template = PromptTemplate(template=prompt_template, input_variables=["text"])
    chain = load_summarize_chain(LLM, chain_type="stuff", prompt=summary_prompt_template, verbose=DEBUG_MODE)
    commit_message = chain.run([changes_summary])
    # Clean up commit message
    commit_message = f"🧞: {commit_message.strip()}"
    quiet_print(f"[{COMMS_COLOR}]Generated commit message:[/{COMMS_COLOR}]{commit_message}")
    return commit_message


def generate_commit_command(commit_message: str = None):
    commit_command = f"git commit -m '{commit_message}'"
    quiet_print(f"[{COMMS_COLOR}]Generated commit command:[/{COMMS_COLOR}]{commit_command}")
    return commit_command


@app.command()
def main(
    instruction: str = typer.Argument(..., help="Human-readable git instruction."),
    execute: bool = typer.Option(False, "--execute", "-x", help="Execute generated git command automatically."),
    explain: bool = typer.Option(
        False,
        "--explain",
        "-e",
        help="Explain the generated git command automatically.",
    ),
    debug: bool = typer.Option(False, "--debug", "-d", help="Debug mode."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode. Just print the generated git command."),
    just_print_commit_message: bool = typer.Option(
        False, "--just-print-commit-message", "-j", help="Just print the generated commit message."
    ),
):
    if debug:
        global DEBUG_MODE
        DEBUG_MODE = True  # noqa: F841
    if quiet or just_print_commit_message:
        global QUIET_MODE
        QUIET_MODE = True  # noqa: F841
    if instruction == "commit":
        diff = get_diff()
        commit_message = generate_commit_message(diff=diff)
        if just_print_commit_message:
            print(commit_message)
            exit(0)
        generated_git_command = generate_commit_command(commit_message=commit_message)
    else:
        generated_git_command = generate_git_command(instruction)
    if quiet:
        print(generated_git_command)
        exit(0)
    if explain:
        explain_git_command(generated_git_command)
    if execute:
        execute_git_command(git_command=generated_git_command)
    if not execute and not explain:
        action = typer.prompt("(E)xplain or e(X)ecute or (N)ew?")
        if action == "E":
            explain_git_command(generated_git_command)
            action = typer.prompt("e(X)ecute or (N)ew?")
            if action == "X":
                execute_git_command(git_command=generated_git_command)
            elif action == "N":
                main(
                    instruction=typer.prompt("Enter new instructions"),
                    execute=False,
                    explain=False,
                )
        elif action == "X":
            execute_git_command(git_command=generated_git_command)
        elif action == "N":
            main(
                instruction=typer.prompt("Enter new instructions"),
                execute=False,
                explain=False,
            )


def update_commit_message(filename: str, mode: str = "append"):
    with open(filename, "r+") as fd:
        contents = fd.readlines()
        commit_msg = contents[0].rstrip("\r\n")

        diff = get_diff()
        gpt_commit_message = generate_commit_message(diff=diff)

        if mode == "append":
            new_commit_msg = f"{commit_msg}\n{gpt_commit_message}"
        elif mode == "replace":
            new_commit_msg = gpt_commit_message
        else:
            raise ValueError(f"Invalid mode: {mode}")

        contents[0] = f"{new_commit_msg}\n"
        fd.seek(0)
        fd.writelines(contents)
        fd.truncate()


append = "append"
replace = "replace"


def pre_commit(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="+")
    parser.add_argument("--mode", nargs="?", const=append, default=append, choices=[append, replace])
    args = parser.parse_args(argv)
    update_commit_message(args.filenames[0], mode=args.mode)


if __name__ == "__main__":
    app()
