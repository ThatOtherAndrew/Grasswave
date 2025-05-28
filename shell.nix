{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    pkgs.mermaid-cli
    pkgs.presenterm
    pkgs.typst

    (pkgs.python312.withPackages (pypkgs: with pypkgs; [
      aiohttp
      fastapi
      lark
      numpy
      pyaudio
      python-rtmidi
      soundfile
      textual
      typer
      uvicorn
    ]))
  ];
}
