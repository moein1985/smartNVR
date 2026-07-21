import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'server_config_provider.dart';

class TimeSyncState {
  final Duration? skew;
  final DateTime? serverTime;
  final bool isChecking;
  final String? error;

  const TimeSyncState({
    this.skew,
    this.serverTime,
    this.isChecking = false,
    this.error,
  });

  bool get hasSignificantSkew =>
      skew != null && skew!.abs() > const Duration(minutes: 2);

  TimeSyncState copyWith({
    Duration? skew,
    DateTime? serverTime,
    bool? isChecking,
    String? error,
  }) {
    return TimeSyncState(
      skew: skew ?? this.skew,
      serverTime: serverTime ?? this.serverTime,
      isChecking: isChecking ?? this.isChecking,
      error: error,
    );
  }
}

final timeSyncProvider =
    NotifierProvider<TimeSyncNotifier, TimeSyncState>(TimeSyncNotifier.new);

class TimeSyncNotifier extends Notifier<TimeSyncState> {
  Timer? _timer;

  @override
  TimeSyncState build() {
    ref.onDispose(() => _timer?.cancel());
    Future.microtask(() => checkSync());
    _timer = Timer.periodic(const Duration(minutes: 5), (_) => checkSync());
    return const TimeSyncState(isChecking: true);
  }

  Future<void> checkSync() async {
    state = state.copyWith(isChecking: true, error: null);
    try {
      final apiClient = ref.read(apiClientProvider);
      final health = await apiClient.health();

      final serverTimestamp =
          (health['server_timestamp'] as num?)?.toDouble();
      if (serverTimestamp == null) {
        debugPrint('[TimeSync] Health response missing server_timestamp');
        state = state.copyWith(
          isChecking: false,
          error: 'server_timestamp not available',
        );
        return;
      }

      final clientNow = DateTime.now().millisecondsSinceEpoch / 1000.0;
      final skewSeconds = clientNow - serverTimestamp;
      final skew = Duration(
        milliseconds: (skewSeconds * 1000).round(),
      );

      final serverTime = DateTime.fromMillisecondsSinceEpoch(
        (serverTimestamp * 1000).round(),
        isUtc: true,
      );

      debugPrint(
        '[TimeSync] Skew: ${skew.inSeconds}s '
        '(client: ${clientNow.round()}, server: ${serverTimestamp.round()})',
      );

      state = TimeSyncState(
        skew: skew,
        serverTime: serverTime,
        isChecking: false,
      );
    } catch (e) {
      debugPrint('[TimeSync] Health check failed: $e');
      state = state.copyWith(
        isChecking: false,
        error: e.toString(),
      );
    }
  }

  void stopTimer() {
    _timer?.cancel();
    _timer = null;
  }
}
