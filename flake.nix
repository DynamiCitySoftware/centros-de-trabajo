{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python3.withPackages (ps: [ ps.pyqt6 ps.pytest ]);
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = [ python ];
        shellHook = ''export PYTHONPATH="$PWD/src:$PYTHONPATH"'';
      };

      #nixosModules.default = import ./nix/module.nix;
    };
}