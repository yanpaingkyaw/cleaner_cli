from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from cleaner import __version__
from cleaner.cleaner import execute_clean, scan_rules
from cleaner.config import load_config
from cleaner.rules import resolve_rules
from cleaner.scanner import parse_size


def _collect_flags(**kwargs) -> set[str]:
    selected: set[str] = set()
    for name, enabled in kwargs.items():
        if enabled:
            selected.add(name)
    return selected


@click.command(name="cleaner")
@click.version_option(version=__version__, prog_name="cleaner")
@click.option("--caches", is_flag=True, help="Clean ~/Library/Caches")
@click.option("--logs", is_flag=True, help="Clean ~/Library/Logs")
@click.option("--tmp", is_flag=True, help="Clean temp files ($TMPDIR)")
@click.option("--trash", "clean_trash", is_flag=True, help="Empty ~/.Trash")
@click.option("--xcode", is_flag=True, help="Clean Xcode DerivedData")
@click.option("--simulators", is_flag=True, help="Clean CoreSimulator caches")
@click.option("--safari", is_flag=True, help="Clean Safari browser cache")
@click.option("--chrome", is_flag=True, help="Clean Chrome browser cache")
@click.option("--firefox", is_flag=True, help="Clean Firefox browser cache")
@click.option("--npm", is_flag=True, help="Clean npm cache")
@click.option("--yarn", is_flag=True, help="Clean Yarn cache")
@click.option("--pip", is_flag=True, help="Clean pip cache")
@click.option("--docker", is_flag=True, help="Clean Docker Desktop data")
@click.option("--all", is_flag=True, help="Clean all categories")
@click.option("--force", is_flag=True, help="Enable deletion (dry-run by default)")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt (requires --force)",
)
@click.option(
    "--move-to-trash",
    is_flag=True,
    help="Move items to ~/.Trash instead of permanent deletion (requires --force)",
)
@click.option("--json", "json_output", is_flag=True, help="Output results as JSON")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
@click.option(
    "--exclude",
    multiple=True,
    type=click.Path(exists=False),
    help="Exclude a path from scanning and deletion (repeatable)",
)
@click.option(
    "--threshold",
    default=None,
    help="Only include categories at or above this size (e.g. 10MB, 1GB)",
)
@click.option(
    "--sort-size",
    is_flag=True,
    help="Sort categories by size (largest first)",
)
def cli(
    caches,
    logs,
    tmp,
    clean_trash,
    xcode,
    simulators,
    safari,
    chrome,
    firefox,
    npm,
    yarn,
    pip,
    docker,
    all,
    force,
    yes,
    move_to_trash,
    json_output,
    quiet,
    exclude,
    threshold,
    sort_size,
):
    """macOS system cache & temp file cleaner.

    By default, runs in dry-run mode and shows what would be deleted.
    Use --force to clean. Use --yes with --force to skip confirmation.
    """
    if yes and not force:
        raise click.UsageError("--yes requires --force")
    if move_to_trash and not force:
        raise click.UsageError("--move-to-trash requires --force")

    config = load_config()
    selected = _collect_flags(
        caches=caches,
        logs=logs,
        tmp=tmp,
        trash=clean_trash,
        xcode=xcode,
        simulators=simulators,
        safari=safari,
        chrome=chrome,
        firefox=firefox,
        npm=npm,
        yarn=yarn,
        pip=pip,
        docker=docker,
        all=all,
    )

    if not selected and config.default_flags:
        selected = set(config.default_flags)

    if not selected:
        if not quiet and not json_output:
            click.echo(
                "No cleaning category selected. Use --help for available options.",
                err=True,
            )
            ctx = click.get_current_context()
            click.echo(ctx.get_help())
            ctx.exit(0)
        if json_output:
            click.echo('{"error": "No cleaning category selected"}')
            ctx = click.get_current_context()
            ctx.exit(1)
        raise click.UsageError("No cleaning category selected")

    rules = resolve_rules(selected, extra_rules=list(config.custom_rules))

    exclude_paths = {path.resolve() for path in config.exclude_paths}
    for path_str in exclude:
        exclude_paths.add(Path(path_str).expanduser().resolve())

    threshold_bytes = 0
    if threshold is not None:
        try:
            threshold_bytes = parse_size(threshold)
        except ValueError as exc:
            raise click.UsageError(str(exc)) from exc

    console = Console(quiet=quiet or json_output)
    show_progress = not quiet and not json_output

    items = scan_rules(
        rules,
        exclude_paths,
        console=console,
        show_progress=show_progress,
    )

    if threshold_bytes > 0:
        items = [item for item in items if item.total_bytes >= threshold_bytes]

    execute_clean(
        items,
        force=force,
        yes=yes,
        console=console,
        quiet=quiet,
        json_output=json_output,
        use_trash=move_to_trash,
        sort_by_size=sort_size,
        exclude_paths=exclude_paths,
    )


def main():
    cli()


if __name__ == "__main__":
    main()
