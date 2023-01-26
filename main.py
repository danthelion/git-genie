import dotenv
import typer
from langchain import FewShotPromptTemplate
from langchain import PromptTemplate, OpenAI, LLMChain
import subprocess

dotenv.load_dotenv()

# app = typer.Typer()


# @app.command
def generate_git_command(command: str):
    examples = [
        {
            "instruction": "Revert last 3 commits",
            "command": "git reset --hard HEAD~3",
        },
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
    example_formatter_template = """
    Instructon: {instruction}
    Command: {command}\n
    """
    example_prompt = PromptTemplate(
        input_variables=["instruction", "command"],
        template=example_formatter_template,
    )

    # Finally, we create the `FewShotPromptTemplate` object.
    few_shot_prompt = FewShotPromptTemplate(
        # These are the examples we want to insert into the prompt.
        examples=examples,
        # This is how we want to format the examples when we insert them into the prompt.
        example_prompt=example_prompt,
        # The prefix is some text that goes before the examples in the prompt.
        # Usually, this consists of intructions.
        prefix="Translate the following human-readable instructions into git commands.",
        # The suffix is some text that goes after the examples in the prompt.
        # Usually, this is where the user input will go
        suffix="Human-readable instruction: {input}\nGit command:",
        # The input variables are the variables that the overall prompt expects.
        input_variables=["input"],
        # The example_separator is the string we will use to join the prefix, examples, and suffix together with.
        example_separator="\n\n",
    )

    llm = OpenAI(temperature=0, model_name="text-davinci-003")
    git_command_translator = LLMChain(llm=llm, prompt=few_shot_prompt)
    git_command = git_command_translator(command)["text"]
    print(f"Generated git command: {git_command}")
    action = typer.prompt("(E)xplain or R(run)?")
    if action == "E":
        explain_git_command(llm, git_command)
        action = typer.prompt("(R)un?")
        if action == "R":
            run_git_command(git_command=git_command)
    elif action == "R":
        run_git_command(git_command=git_command)


def explain_git_command(llm, git_command: str):
    # TODO add few shot prompt with one by one explanation
    # git log --graph --decorate --oneline --all --color --7
    # explain every argument line by line
    # Second example:
    # "count how many times test.json was modified in the last week"
    # Generated git command:  git log --since=1.week --name-only --oneline -- test.json | grep test.json | wc -l
    print(f"Explaining command: {git_command}")
    explain_prompt_template = """
    Explain in detail what the following git command does:
    {git_command}
    """
    prompt = PromptTemplate(
        input_variables=["git_command"], template=explain_prompt_template
    )
    explaner = LLMChain(llm=llm, prompt=prompt)
    explanation = explaner(git_command)["text"]
    print(f"Command explanation: {explanation}")


def run_git_command(git_command: str):
    print(f"Running command: {git_command}")
    # TODO parse correctly and run, propagate output
    subprocess.run(git_command, shell=True)


if __name__ == "__main__":
    typer.run(generate_git_command)
