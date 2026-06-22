#!/usr/bin/env python3
"""Update the Homebrew formula with release version and binary checksums."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: update_homebrew_formula.py VERSION SHA_X86 SHA_ARM")

    version, sha_x86, sha_arm = sys.argv[1:4]
    formula = f'''class CleanerCli < Formula
  desc "macOS system cache & temp file cleaner CLI"
  homepage "https://github.com/yanpaingkyaw/cleaner_cli"
  version "{version}"
  license "MIT"

  if Hardware::CPU.intel?
    url "https://github.com/yanpaingkyaw/cleaner_cli/releases/download/v{version}/cleaner-darwin-x86_64"
    sha256 "{sha_x86}"
  else
    url "https://github.com/yanpaingkyaw/cleaner_cli/releases/download/v{version}/cleaner-darwin-arm64"
    sha256 "{sha_arm}"
  end

  def install
    arch = Hardware::CPU.intel? ? "x86_64" : "arm64"
    bin.install "cleaner-darwin-#{{arch}}" => "cleaner"
  end

  test do
    system "#{{bin}}/cleaner", "--version"
  end
end
'''
    output = Path("homebrew/cleaner-cli.rb")
    output.write_text(formula, encoding="utf-8")
    print(f"Updated {output}")


if __name__ == "__main__":
    main()
