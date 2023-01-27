import subprocess

import typer
from langchain import FewShotPromptTemplate
from langchain import PromptTemplate, OpenAI, LLMChain
from rich import print

LLM = OpenAI(temperature=0, model_name="text-davinci-003")

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
]

EXPLAIN_GIT_COMMAND_EXAMPLES = [
    {
        "command": 'git rebase -i HEAD~5 --autosquash -m "legacy code"',
        "explanation": "git rebase[/bold red] -> Forward-port local commits to the updated upstream head\n"
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
        "command": " git log --graph --decorate --oneline --all -n 5",
        "explanation": "git log -> Show commit logs\n--graph -> Show an ASCII graph of the branch and merge"
        "history beside the log output\n--decorate -> Show the ref names of any commits that are"
        "shown\n--oneline -> Show only the first line of each commit message\n--all ->"
        "Show all commits, including those that are not reachable from any branch\n-n 5 ->"
        "Show only the last 5 commits",
    },
]

app = typer.Typer()


@app.command()
def generate_git_command(command: str):
    example_formatter_template = """
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
    git_command = git_command_translator(command)["text"]
    print(f"Generated git command: {git_command}")
    action = typer.prompt("(E)xplain or R(run)?")
    if action == "E":
        explain_git_command(git_command)
        action = typer.prompt("(R)un?")
        if action == "R":
            run_git_command(git_command=git_command)
    elif action == "R":
        run_git_command(git_command=git_command)


def explain_git_command(git_command: str):
    explain_example_formatter_template = """
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
        example_separator="\n\n",
    )

    git_command_translator = LLMChain(llm=LLM, prompt=explain_few_shot_prompt)
    explanation = git_command_translator(git_command)["text"]
    print(f"Explanation\n{explanation}")


def run_git_command(git_command: str):
    print(f"Running command: {git_command}")
    subprocess.run(git_command, shell=True)


if __name__ == "__main__":
    typer.run(generate_git_command)
