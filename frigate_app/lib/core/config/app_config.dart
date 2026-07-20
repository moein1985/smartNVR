class ServerConfig {
  final String ip;
  final int port;

  const ServerConfig({required this.ip, required this.port});

  String get baseUrl => 'http://$ip:$port';

  @override
  bool operator ==(Object other) =>
      other is ServerConfig && other.ip == ip && other.port == port;

  @override
  int get hashCode => Object.hash(ip, port);

  @override
  String toString() => 'ServerConfig(ip: $ip, port: $port)';
}
