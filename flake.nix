{
  description = "MA2006B Reto FJ26";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/25.11";
    nixpkgs-21-05.url = "github:NixOS/nixpkgs/21.05"; # Last release with Python 3.6
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, nixpkgs-21-05, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        pkgs-21-05 = import nixpkgs-21-05 { inherit system; };
        python = pkgs-21-05.python36;
        pythonEnv = python.withPackages (ps: with ps; [
          # Backend API
          flask
          flask-restx
          flask-swagger-ui

          # Backend Database
          tinydb

          # Cryptography
          cryptography
          bcrypt
        ]);
      in {
        apps.default = {
          type = "app";
          program = toString (pkgs.writeShellScript "run" ''
            FLASK_APP=src/backend/main.py ${pythonEnv}/bin/flask run --port 8000
          '');
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv pkgs.openssl ];
          shellHook = ''
            export PS1="[dev] \u@\h:\w$ "
          '';
        };
      }
    );
}
