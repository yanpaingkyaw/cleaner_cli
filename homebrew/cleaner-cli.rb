class CleanerCli < Formula
  desc "macOS system cache & temp file cleaner CLI"
  homepage "https://github.com/yanpaingkyaw/cleaner_cli"
  version "0.2.0"
  license "MIT"

  if Hardware::CPU.intel?
    url "https://github.com/yanpaingkyaw/cleaner_cli/releases/download/v0.2.0/cleaner-darwin-x86_64"
    sha256 "pending-release"
  else
    url "https://github.com/yanpaingkyaw/cleaner_cli/releases/download/v0.2.0/cleaner-darwin-arm64"
    sha256 "pending-release"
  end

  def install
    arch = Hardware::CPU.intel? ? "x86_64" : "arm64"
    bin.install "cleaner-darwin-#{arch}" => "cleaner"
  end

  test do
    system "#{bin}/cleaner", "--version"
  end
end
