{ pkgs, posPython, ... }:

let
  pythonConPyQt = pkgs.python3.withPackages (ps: with ps; [ pyqt6 ]);

  ventaScript = pkgs.writeShellScriptBin "interfaz-venta" ''
    export DISPLAY=:0
    export XAUTHORITY=/home/pos001/.Xauthority
    exec ${pythonConPyQt}/bin/python ${./bin/interfaz_principal.py}
  '';

in {
  environment.systemPackages = [ ventaScript pythonConPyQt ];

  systemd.user.services.interfaz-pos = {
    description = "Servicio Kiosco de Venta";
    wantedBy = [ "graphical-session.target" ];
    partOf = [ "graphical-session.target" ];

    serviceConfig = {
      ExecStart = "${ventaScript}/bin/interfaz-venta";
      Restart = "always";
      RestartSec = "30s";
    };
  };
}