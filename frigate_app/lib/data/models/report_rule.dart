class ReportRule {
  final String id;
  final String name;
  final bool enabled;
  final List<String> zones;
  final List<String> cameras;
  final List<String> labels;
  final int intervalHours;
  final String timezone;
  final String destination;
  final String chatId;
  final String promptTemplate;
  final bool includeSummary;
  final bool includeRawData;
  final String createdAt;
  final String lastRun;
  final String lastStatus;

  ReportRule({
    required this.id,
    required this.name,
    this.enabled = true,
    this.zones = const [],
    this.cameras = const [],
    this.labels = const [],
    this.intervalHours = 24,
    this.timezone = 'Asia/Tehran',
    this.destination = 'telegram',
    this.chatId = '',
    this.promptTemplate = '',
    this.includeSummary = true,
    this.includeRawData = false,
    this.createdAt = '',
    this.lastRun = '',
    this.lastStatus = '',
  });

  factory ReportRule.fromJson(Map<String, dynamic> json) {
    return ReportRule(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      enabled: json['enabled'] as bool? ?? true,
      zones: (json['zones'] as List?)?.cast<String>() ?? [],
      cameras: (json['cameras'] as List?)?.cast<String>() ?? [],
      labels: (json['labels'] as List?)?.cast<String>() ?? [],
      intervalHours: json['interval_hours'] as int? ?? 24,
      timezone: json['timezone'] as String? ?? 'Asia/Tehran',
      destination: json['destination'] as String? ?? 'telegram',
      chatId: json['chat_id'] as String? ?? '',
      promptTemplate: json['prompt_template'] as String? ?? '',
      includeSummary: json['include_summary'] as bool? ?? true,
      includeRawData: json['include_raw_data'] as bool? ?? false,
      createdAt: json['created_at'] as String? ?? '',
      lastRun: json['last_run'] as String? ?? '',
      lastStatus: json['last_status'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'enabled': enabled,
      'zones': zones,
      'cameras': cameras,
      'labels': labels,
      'interval_hours': intervalHours,
      'timezone': timezone,
      'destination': destination,
      'chat_id': chatId,
      'prompt_template': promptTemplate,
      'include_summary': includeSummary,
      'include_raw_data': includeRawData,
    };
  }

  ReportRule copyWith({
    String? id,
    String? name,
    bool? enabled,
    List<String>? zones,
    List<String>? cameras,
    List<String>? labels,
    int? intervalHours,
    String? timezone,
    String? destination,
    String? chatId,
    String? promptTemplate,
    bool? includeSummary,
    bool? includeRawData,
    String? createdAt,
    String? lastRun,
    String? lastStatus,
  }) {
    return ReportRule(
      id: id ?? this.id,
      name: name ?? this.name,
      enabled: enabled ?? this.enabled,
      zones: zones ?? this.zones,
      cameras: cameras ?? this.cameras,
      labels: labels ?? this.labels,
      intervalHours: intervalHours ?? this.intervalHours,
      timezone: timezone ?? this.timezone,
      destination: destination ?? this.destination,
      chatId: chatId ?? this.chatId,
      promptTemplate: promptTemplate ?? this.promptTemplate,
      includeSummary: includeSummary ?? this.includeSummary,
      includeRawData: includeRawData ?? this.includeRawData,
      createdAt: createdAt ?? this.createdAt,
      lastRun: lastRun ?? this.lastRun,
      lastStatus: lastStatus ?? this.lastStatus,
    );
  }
}
