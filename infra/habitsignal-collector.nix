# infra/habitsignal-collector.nix
# NixOS systemd サービス定義
# configuration.nix から imports に追加して使う

{ config, pkgs, ... }:

{
  systemd.services.habitsignal-collector = {
    description = "HabitSignal MQTT Collector";
    after = [ "network.target" "mosquitto.service" "mongodb.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/habitsignal/collector/main.py";
      WorkingDirectory = "/var/lib/habitsignal/collector";
      EnvironmentFile = "/var/lib/habitsignal/collector/.env";
      Restart = "on-failure";
      RestartSec = "5s";
      User = "habitsignal";
    };
  };

  # Mosquitto ブローカー
  services.mosquitto = {
    enable = true;
    listeners = [
      {
        port = 1883;
        address = "0.0.0.0";
        settings.allow_anonymous = true;
      }
    ];
  };

  # MongoDB
  services.mongodb = {
    enable = true;
    bind_ip = "127.0.0.1";
  };

  # サービス実行ユーザー
  users.users.habitsignal = {
    isSystemUser = true;
    group = "habitsignal";
  };
  users.groups.habitsignal = {};
}
