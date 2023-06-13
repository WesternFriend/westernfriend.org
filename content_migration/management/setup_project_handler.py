from django.core.management import call_command


def setup_project() -> None:
    # Call the migrate command
    call_command(
        "migrate",
    )

    # call the scaffold initial content command
    call_command(
        "scaffold_initial_content",
    )
