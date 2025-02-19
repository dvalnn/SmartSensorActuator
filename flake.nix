{
  description = "Micropython dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        openfw = pkgs.writeShellScriptBin "openfw" ''
          sudo iptables -A INPUT -p tcp --dport 1883 -j ACCEPT
          sudo systemctl reload firewall
        '';

        closefw = pkgs.writeShellScriptBin "closefw" ''
          sudo iptables -D INPUT -p tcp --dport 1883 -j ACCEPT
          sudo systemctl reload firewall
        '';

        upload = pkgs.writeShellScriptBin "upload" ''
          mkdir -p ./micropython/temp
          cat ./micropython/config/config.json | jq -c > ./micropython/temp/config.json
          cat ./micropython/config/secrets.json | jq -c > ./micropython/temp/secrets.json

          mpremote mkdir :config
          mpremote cp -r ./micropython/temp/* :config
          mpremote cp -r ./micropython/src/ :

          rm -rf ./micropython/temp
        '';

        run = pkgs.writeShellScriptBin "run" ''
          mpremote run ./micropython/src/main.py
        '';

        flash = pkgs.writeShellScriptBin "flash" ''
          upload
          mpremote cp -r ./micropython/boot.py :
        '';

        nuke = pkgs.writeShellScriptBin "nuke" ''
          mpremote run ./micropython/_nuke.py
        '';
      in
      {
        devShells.default = pkgs.mkShell {
          shellHook = ''
            export PATH=$PATH:$(pwd)/api/node_modules/.bin
          '';
          buildInputs = with pkgs; [
            # helper scripts

            # temporarily open/close firewall for mqtt
            openfw
            closefw

            # micropython utils
            upload
            run
            flash
            nuke

            jq # json cli parser

            mpremote # micropython remote tool
            mosquitto # mqtt broker

            # to install asyncapi cli
            nodejs_23
            # edge node development
            deno # dev tools and runtime
          ];
        };
      }
    );
}
