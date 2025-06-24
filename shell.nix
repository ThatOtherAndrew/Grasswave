{pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python312;
  buildInputs = with pkgs; [
    stdenv.cc.cc
    portaudio
  ];
in
  pkgs.mkShell {
    packages = with pkgs; [
      (python.withPackages (pypkgs: with pypkgs; [
        uv
      ]))
    ];

    shellHook = ''
      export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath buildInputs}
      export UV_PYTHON_DOWNLOADS=never
      export UV_USE_MANAGED_PYTHON=0

      export CFLAGS="-I${pkgs.portaudio}/include"
      export LDFLAGS="-L${pkgs.portaudio}/lib"

      source .venv/bin/activate
    '';
  }
