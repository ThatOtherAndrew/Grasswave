{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python312;
  buildInputs = with pkgs; [
    stdenv.cc.cc
    portaudio
  ];
in
  pkgs.mkShell {
    name = "grasswave";

    packages = with pkgs; [
      (python.withPackages (pypkgs: with pypkgs; [
        uv
      ]))
    ];

    shellHook = ''
      export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath buildInputs}
      export UV_NO_MANAGED_PYTHON=1
      export UV_PYTHON_DOWNLOADS=never

      export CFLAGS="-I${pkgs.portaudio}/include"
      export LDFLAGS="-L${pkgs.portaudio}/lib"

      alias uv='UV_PYTHON=$(which python) uv'

      source .venv/bin/activate
    '';
  }
