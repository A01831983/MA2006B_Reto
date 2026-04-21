{
  description = "MA2006B Reto FJ26";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/21.05"; # Last release with Python 3.6
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python36;
        pythonEnv = python.withPackages (ps: with ps; [
          flask
          flask-restx
          cryptography
        ]);
        launch-backend = pkgs.stdenv.mkDerivation {
          pname = "launch-backend";
          version = "0.1.0";

          src = ./src/backend;

          buildInputs = [ pythonEnv ];

          installPhase = ''
            mkdir -p $out/bin
            cp main.py $out/bin/launch-backend
            chmod +x $out/bin/launch-backend
            patchShebangs $out/bin/launch-backend
          '';
        };
      in {
        packages.default = launch-backend;

        apps.default = flake-utils.lib.mkApp {
          drv = launch-backend;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
        };
      }
    );
}
