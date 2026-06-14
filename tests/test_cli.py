import pytest
from click.testing import CliRunner
from cleaner.cli import cli

runner = CliRunner()


def test_cli_no_args():
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "No cleaning category selected" in result.output


def test_cli_help():
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--caches" in result.output
    assert "--force" in result.output
    assert "--yes" in result.output


def test_cli_version():
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "cleaner" in result.output


def test_cli_dry_run_all():
    result = runner.invoke(cli, ["--all"])
    assert result.exit_code == 0
    assert "Dry run" in result.output
    assert "Use --force to clean" in result.output


def test_cli_yes_without_force():
    result = runner.invoke(cli, ["--all", "--yes"])
    assert result.exit_code != 0
    assert "--yes requires --force" in result.output
