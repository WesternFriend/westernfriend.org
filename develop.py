import argparse
import subprocess

COMMANDS = {
    "compile-deps": [
        "python -m piptools compile --resolver backtracking -o requirements.txt pyproject.toml",  # noqa: E501
        "python -m piptools compile --extra dev --resolver backtracking -o requirements-dev.txt pyproject.toml",  # noqa: E501
        "rm -rf Western_Friend_website.egg-info",
    ],
    "start-db": [
        "colima start && docker-compose up -d",
    ],
    "install": [
        "python -m pip install -r requirements.txt -r requirements-dev.txt",
    ],
    "test": [
        "python manage.py test",
    ],
    "update-deps": [
        "pre-commit autoupdate",
        "python -m pip install --upgrade pip-tools pip wheel",
        "python -m piptools compile --upgrade --resolver backtracking -o requirements.txt pyproject.toml",  # noqa: E501
        "python -m piptools compile --extra dev --upgrade --resolver backtracking -o requirements-dev.txt pyproject.toml",  # noqa: E501
        "python -m pip check",
    ],
}


def run_commands(
    commands: list[str],
) -> None:
    for command in commands:
        process = subprocess.run(
            command,
            shell=True,
            check=True,
        )
        process.check_returncode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Development tasks.")
    parser.add_argument("command", choices=COMMANDS.keys(), help="The command to run.")
    args = parser.parse_args()

    run_commands(COMMANDS[args.command])
