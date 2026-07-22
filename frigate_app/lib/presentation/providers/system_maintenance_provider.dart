import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/server_config_provider.dart';

enum UpdateState { idle, uploading, success, rolledBack, failed }

class SystemMaintenanceState {
  final UpdateState updateState;
  final String? logs;
  final String? message;
  final bool isLoadingLogs;

  const SystemMaintenanceState({
    this.updateState = UpdateState.idle,
    this.logs,
    this.message,
    this.isLoadingLogs = false,
  });

  SystemMaintenanceState copyWith({
    UpdateState? updateState,
    String? logs,
    String? message,
    bool? isLoadingLogs,
  }) {
    return SystemMaintenanceState(
      updateState: updateState ?? this.updateState,
      logs: logs ?? this.logs,
      message: message ?? this.message,
      isLoadingLogs: isLoadingLogs ?? this.isLoadingLogs,
    );
  }
}

class SystemMaintenanceNotifier extends Notifier<SystemMaintenanceState> {
  @override
  SystemMaintenanceState build() => const SystemMaintenanceState();

  Future<void> fetchLogs({int lines = 100}) async {
    state = state.copyWith(isLoadingLogs: true);
    try {
      final client = ref.read(apiClientProvider);
      final logs = await client.getSystemLogs(lines);
      state = state.copyWith(logs: logs, isLoadingLogs: false);
    } catch (e) {
      state = state.copyWith(
        isLoadingLogs: false,
        logs: 'خطا در دریافت لاگ‌ها: $e',
      );
    }
  }

  Future<void> uploadUpdate(String filePath) async {
    state = state.copyWith(updateState: UpdateState.uploading);
    try {
      final client = ref.read(apiClientProvider);
      final result = await client.uploadUpdate(File(filePath));
      final status = result['status'] as String?;
      if (status == 'ok') {
        state = state.copyWith(
          updateState: UpdateState.success,
          message: result['message'] as String? ?? 'به‌روزرسانی موفق بود',
        );
      } else if (status == 'rolled_back') {
        state = state.copyWith(
          updateState: UpdateState.rolledBack,
          message:
              result['message'] as String? ?? 'به‌روزرسانی بازگردانده شد',
        );
      } else {
        state = state.copyWith(
          updateState: UpdateState.failed,
          message: result['message'] as String? ?? 'به‌روزرسانی ناموفق بود',
        );
      }
    } catch (e) {
      state = state.copyWith(
        updateState: UpdateState.failed,
        message: 'خطا در به‌روزرسانی: $e',
      );
    }
  }

  void reset() {
    state = const SystemMaintenanceState();
  }
}

final systemMaintenanceProvider =
    NotifierProvider<SystemMaintenanceNotifier, SystemMaintenanceState>(
  SystemMaintenanceNotifier.new,
);
