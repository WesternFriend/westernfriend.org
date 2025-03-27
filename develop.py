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
        alias="start-db",
        help_text="Start the database",
        commands_list=[
            "docker compose up -d wf_postgres_service",
        ],
    ),
    Command(
        alias="stop-db",
        help_text="Stop the database",
        commands_list=[
            "docker compose stop wf_postgres_service",
        ],
    ),
    Command(
        alias="reset-db",
        help_text="Reset the database",
        commands_list=[
            "python manage.py reset_db --noinput -c",
            "python manage.py migrate",
        ],
    ),
    Command(
        alias="scaffold-db",
        help_text="Scaffold initial database content",
        commands_list=[
            "python manage.py scaffold_initial_content",
        ],
    ),
    Command(
        alias="test",
        help_text="Run tests",
        commands_list=[
            "python manage.py test",
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
