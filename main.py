import json
from pathlib import Path

import dotenv
import typer
from langchain import FewShotPromptTemplate
from langchain import PromptTemplate, OpenAI, LLMChain
import subprocess

dotenv.load_dotenv()

# app = typer.Typer()

EXAMPLES = Path("examples")
LLM = OpenAI(temperature=0, model_name="text-davinci-003")


# @app.command
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
        examples=json.load((EXAMPLES / "generate_git_command_examples.json").open()),
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
        examples=json.load((EXAMPLES / "explain_git_command_examples.json").open()),
        example_prompt=explain_example_prompt,
        prefix="Explain the followng git command.",
        suffix="Git command: {input}\nExplanation:",
        input_variables=["input"],
        example_separator="\n\n",
    )

    git_command_translator = LLMChain(llm=LLM, prompt=explain_few_shot_prompt)
    explanation = git_command_translator(git_command)["text"]
    print(f"Generated explanation: {explanation}")


def run_git_command(git_command: str):
    print(f"Running command: {git_command}")
    # TODO parse correctly and run, propagate output
    subprocess.run(git_command, shell=True)


if __name__ == "__main__":
    typer.run(generate_git_command)
