# Reproducible shell for Task 1: LangGraph + LangChain(OpenAI) on Python 3.13.
# Usage:  nix-shell --impure --run "python agent_network.py --input data/corpus --output output"
# Uses the nixpkgs flake registry (no channel needed); --impure required for getFlake.
{
  pkgs ? import (builtins.getFlake "nixpkgs") { }
}:
pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (ps: with ps; [
      langgraph
      langchain-openai
    ]))
  ];
}
