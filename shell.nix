{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    mermaid-cli
    presenterm
    typst

    (python312.withPackages (pypkgs: with pypkgs; [
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
