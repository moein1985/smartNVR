import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/report_rule.dart';
import 'server_config_provider.dart';

class ReportRulesState {
  final List<ReportRule> rules;
  final bool isLoading;
  final String? error;

  const ReportRulesState({
    this.rules = const [],
    this.isLoading = false,
    this.error,
  });

  ReportRulesState copyWith({
    List<ReportRule>? rules,
    bool? isLoading,
    String? error,
  }) {
    return ReportRulesState(
      rules: rules ?? this.rules,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class ReportRulesNotifier extends Notifier<ReportRulesState> {
  @override
  ReportRulesState build() {
    Future.microtask(() => _loadRules());
    return const ReportRulesState(isLoading: true);
  }

  Future<void> _loadRules() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final client = ref.read(apiClientProvider);
      final rules = await client.getReportRules();
      state = ReportRulesState(rules: rules, isLoading: false);
    } catch (e) {
      debugPrint('[ReportRules] Failed to load rules: $e');
      state = ReportRulesState(
        isLoading: false,
        error: 'خطا در دریافت قوانین: $e',
      );
    }
  }

  Future<void> createRule(Map<String, dynamic> payload) async {
    try {
      final client = ref.read(apiClientProvider);
      final rule = await client.createReportRule(payload);
      state = state.copyWith(rules: [...state.rules, rule]);
    } catch (e) {
      debugPrint('[ReportRules] Failed to create rule: $e');
      state = state.copyWith(error: 'خطا در ایجاد قانون: $e');
    }
  }

  Future<void> updateRule(String id, Map<String, dynamic> payload) async {
    try {
      final client = ref.read(apiClientProvider);
      final updated = await client.updateReportRule(id, payload);
      state = state.copyWith(
        rules: state.rules.map((r) => r.id == id ? updated : r).toList(),
      );
    } catch (e) {
      debugPrint('[ReportRules] Failed to update rule: $e');
      state = state.copyWith(error: 'خطا در به‌روزرسانی قانون: $e');
    }
  }

  Future<void> deleteRule(String id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.deleteReportRule(id);
      state = state.copyWith(
        rules: state.rules.where((r) => r.id != id).toList(),
      );
    } catch (e) {
      debugPrint('[ReportRules] Failed to delete rule: $e');
      state = state.copyWith(error: 'خطا در حذف قانون: $e');
    }
  }

  Future<void> testRun(String id) async {
    try {
      final client = ref.read(apiClientProvider);
      await client.testRunRule(id);
    } catch (e) {
      debugPrint('[ReportRules] Test run failed: $e');
      state = state.copyWith(error: 'خطا در اجرای آزمایشی: $e');
    }
  }

  Future<void> refresh() async => _loadRules();
}

final reportRulesProvider =
    NotifierProvider<ReportRulesNotifier, ReportRulesState>(
  ReportRulesNotifier.new,
);
