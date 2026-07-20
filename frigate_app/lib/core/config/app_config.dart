class ServerConfig {
  final String ip;
  final int port;
  final bool isMockMode;

  const ServerConfig({
    required this.ip,
    required this.port,
    this.isMockMode = false,
  });

  ServerConfig copyWith({String? ip, int? port, bool? isMockMode}) {
    return ServerConfig(
      ip: ip ?? this.ip,
      port: port ?? this.port,
      isMockMode: isMockMode ?? this.isMockMode,
    );
  }

  String get baseUrl => 'http://$ip:$port';

  @override
  bool operator ==(Object other) =>
      other is ServerConfig &&
      other.ip == ip &&
      other.port == port &&
      other.isMockMode == isMockMode;

  @override
  int get hashCode => Object.hash(ip, port, isMockMode);

  @override
  String toString() =>
      'ServerConfig(ip: $ip, port: $port, isMockMode: $isMockMode)';
}
