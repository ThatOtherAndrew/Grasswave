{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python312;
  buildInputs = with pkgs; [
    stdenv.cc.cc
    portaudio

    # OpenCV
    libGL
    glib

    # Qt/X11 for OpenCV GUI - comprehensive dependencies for xcb
    xorg.libX11
    xorg.libXext
    xorg.libxcb
    xorg.libXrender
    xorg.libXi
    xorg.libSM
    xorg.libICE
    xorg.xcbutil
    xorg.xcbutilimage
    xorg.xcbutilkeysyms
    xorg.xcbutilrenderutil
    xorg.xcbutilwm
    libxkbcommon
    fontconfig
    freetype
    dbus
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

      # Qt plugin path for OpenCV
      export QT_PLUGIN_PATH="${pkgs.qt5.qtbase}/lib/qt-${pkgs.qt5.qtbase.version}/plugins"
      export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt5.qtbase}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/platforms"

      alias uv='UV_PYTHON=$(which python) uv'

      source .venv/bin/activate
    '';
  }
