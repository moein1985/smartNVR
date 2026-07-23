import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/server_config_provider.dart';

class OrchestratorState {
  final Map<String, dynamic>? hardware;
  final List<dynamic> containers;
  final bool isLoadingHardware;
  final bool isLoadingContainers;
  final String? error;

  const OrchestratorState({
    this.hardware,
    this.containers = const [],
    this.isLoadingHardware = false,
    this.isLoadingContainers = false,
    this.error,
  });

  OrchestratorState copyWith({
    Map<String, dynamic>? hardware,
    List<dynamic>? containers,
    bool? isLoadingHardware,
    bool? isLoadingContainers,
    String? error,
  }) {
    return OrchestratorState(
      hardware: hardware ?? this.hardware,
      containers: containers ?? this.containers,
      isLoadingHardware: isLoadingHardware ?? this.isLoadingHardware,
      isLoadingContainers: isLoadingContainers ?? this.isLoadingContainers,
      error: error,
    );
  }
}

class OrchestratorNotifier extends Notifier<OrchestratorState> {
  @override
  OrchestratorState build() => const OrchestratorState();

  Future<void> fetchHardware() async {
    state = state.copyWith(isLoadingHardware: true, error: null);
    try {
      final client = ref.read(apiClientProvider);
      final hw = await client.getHardware();
      state = state.copyWith(hardware: hw, isLoadingHardware: false);
    } catch (e) {
      debugPrint('[Orchestrator] Failed to fetch hardware: $e');
      state = state.copyWith(
        isLoadingHardware: false,
        error: 'خطا در دریافت اطلاعات سخت‌افزار: $e',
      );
    }
  }

  Future<void> fetchContainers() async {
    state = state.copyWith(isLoadingContainers: true, error: null);
    try {
      final client = ref.read(apiClientProvider);
      final result = await client.getContainers();
      final list = result['containers'] as List? ?? [];
      state = state.copyWith(containers: list, isLoadingContainers: false);
    } catch (e) {
      debugPrint('[Orchestrator] Failed to fetch containers: $e');
      state = state.copyWith(
        isLoadingContainers: false,
        error: 'خطا در دریافت کانتینرها: $e',
      );
    }
  }

  Future<void> refreshAll() async {
    await Future.wait([fetchHardware(), fetchContainers()]);
  }
}

final orchestratorProvider =
    NotifierProvider<OrchestratorNotifier, OrchestratorState>(
  OrchestratorNotifier.new,
);
