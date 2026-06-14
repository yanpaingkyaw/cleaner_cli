import click
from rich.console import Console

from cleaner import __version__
from cleaner.cleaner import execute_clean, scan_rules
from cleaner.rules import resolve_rules


@click.command(name="cleaner")
@click.version_option(version=__version__, prog_name="cleaner")
@click.option("--caches", is_flag=True, help="Clean ~/Library/Caches")
@click.option("--logs", is_flag=True, help="Clean ~/Library/Logs")
@click.option("--tmp", is_flag=True, help="Clean temp files ($TMPDIR)")
@click.option("--trash", is_flag=True, help="Empty the Trash")
@click.option("--xcode", is_flag=True, help="Clean Xcode DerivedData")
@click.option("--all", is_flag=True, help="Clean all categories")
@click.option("--force", is_flag=True, help="Enable deletion (dry-run by default)")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt (requires --force)",
)
def cli(caches, logs, tmp, trash, xcode, all, force, yes):
    """macOS system cache & temp file cleaner.

    By default, runs in dry-run mode and shows what would be deleted.
    Use --force to clean. Use --yes with --force to skip confirmation.
    """
    if yes and not force:
        raise click.UsageError("--yes requires --force")

    selected: set[str] = set()
    if caches:
        selected.add("caches")
    if logs:
        selected.add("logs")
    if tmp:
        selected.add("tmp")
    if trash:
        selected.add("trash")
    if xcode:
        selected.add("xcode")
    if all:
        selected.add("all")

    if not selected:
        click.echo(
            "No cleaning category selected. Use --help for available options.",
            err=True,
        )
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(0)

    rules = resolve_rules(selected)
    items = scan_rules(rules)
    console = Console()
    execute_clean(items, force=force, yes=yes, console=console)


def main():
    cli()
