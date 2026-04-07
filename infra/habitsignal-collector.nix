# infra/habitsignal-collector.nix
# NixOS service definition (reference)
# Actual deployment lives in dotfiles as a NixOS module with sops-nix secrets.

{ config, pkgs, lib, ... }:
let
  cfg = config.yktsnet.apps.habitsignal;
  homeDir = config.users.users.yktsnet.home;
  appRoot = "${homeDir}/dotfiles/apps/habitsignal/server/collector";
  envFile = config.sops.secrets."habitsignal/habitsignal.env".path;

  appEnv = pkgs.python3.withPackages (ps: with ps; [
    paho-mqtt
    psycopg2
  ]);
in
{
  options.yktsnet.apps.habitsignal = {
    enable = lib.mkEnableOption "HabitSignal";
    collector = lib.mkEnableOption "MQTT -> PostgreSQL collector";
  };

  config = lib.mkIf cfg.enable {

    # Mosquitto MQTT broker
    services.mosquitto = {
      enable = true;
      listeners = [{
        port = 1883;
        address = "0.0.0.0";
        settings.allow_anonymous = true;
        acl = [ "topic readwrite #" ];
      }];
    };

    # PostgreSQL: habitsignal DB and user
    # services.postgresql is already enabled in het/system.nix
    services.postgresql.ensureDatabases = [ "habitsignal" ];
    services.postgresql.ensureUsers = [{
      name = "habitsignal";
      ensureDBOwnership = true;
    }];

    # Firewall: open MQTT port
    networking.firewall.allowedTCPPorts = [ 1883 ];

    # Collector service
    systemd.user.services = {
      habitsignal-collector = lib.mkIf cfg.collector {
        description = "HabitSignal MQTT Collector";
        wantedBy = [ "default.target" ];
        after = [ "mosquitto.service" "postgresql.service" ];
        serviceConfig = {
          Type = "simple";
          WorkingDirectory = appRoot;
          EnvironmentFile = envFile;
          ExecStart = "${appEnv}/bin/python3 ${appRoot}/main.py";
          Restart = "on-failure";
          RestartSec = "5s";
        };
      };
    };
  };
}
