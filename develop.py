import argparse
import subprocess
from dataclasses import dataclass


@dataclass
class Command:
    alias: str
    help_text: str
    commands_list: list[str]


COMMANDS = [
    Command(
        alias="compile-deps",
        help_text="Compile the project's dependencies",
        commands_list=[
            "python -m piptools compile --resolver backtracking -o requirements.txt pyproject.toml",  # noqa: E501
            "python -m piptools compile --extra dev --resolver backtracking -o requirements-dev.txt pyproject.toml",  # noqa: E501
            "rm -rf Western_Friend_website.egg-info",
        ],
    ),
    Command(
        alias="start-db",
        help_text="Start the database",
        commands_list=[
            "docker-compose up -d wf_postgres_service",
        ],
    ),
    Command(
        alias="install",
        help_text="Install project dependencies",
        commands_list=[
            "python -m pip install -r requirements.txt -r requirements-dev.txt",
        ],
    ),
    Command(
        alias="test",
        help_text="Run tests",
        commands_list=[
            "python manage.py test",
        ],
    ),
    Command(
        alias="update-deps",
        help_text="Update dependencies and check for issues",
        commands_list=[
            "pre-commit autoupdate",
            "python -m pip install --upgrade pip-tools pip wheel",
            "python -m piptools compile --upgrade --resolver backtracking -o requirements.txt pyproject.toml",  # noqa: E501
            "python -m piptools compile --extra dev --upgrade --resolver backtracking -o requirements-dev.txt pyproject.toml",  # noqa: E501
            "python -m pip check",
        ],
    ),
]


def run_command(command: str) -> None:
    process = subprocess.run(command, shell=True, check=True)
    process.check_returncode()


def run_commands(commands: list[str]) -> None:
    for command in commands:
        run_command(command)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Development tasks.")
    subparsers = parser.add_subparsers()

    for command in COMMANDS:
        subparser = subparsers.add_parser(command.alias, help=command.help_text)
        subparser.set_defaults(commands_list=command.commands_list)

    args = parser.parse_args()

    if "commands_list" in args:
        run_commands(args.commands_list)
    else:
        parser.print_help()
