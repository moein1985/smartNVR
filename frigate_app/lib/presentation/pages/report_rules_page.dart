import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/report_rule.dart';
import '../providers/report_rules_provider.dart';

class ReportRulesPage extends ConsumerStatefulWidget {
  const ReportRulesPage({super.key});

  @override
  ConsumerState<ReportRulesPage> createState() => _ReportRulesPageState();
}

class _ReportRulesPageState extends ConsumerState<ReportRulesPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(reportRulesProvider.notifier).refresh();
    });
  }

  void _showFormModal({ReportRule? rule}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (context) => _ReportRuleFormModal(
        rule: rule,
        onSubmit: (payload) async {
          final navigator = Navigator.of(context);
          if (rule == null) {
            await ref.read(reportRulesProvider.notifier).createRule(payload);
          } else {
            await ref
                .read(reportRulesProvider.notifier)
                .updateRule(rule.id, payload);
          }
          if (mounted) navigator.pop();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(reportRulesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('قوانین گزارش‌گیری'),
        centerTitle: true,
        actions: [
          IconButton(
            onPressed: () => ref.read(reportRulesProvider.notifier).refresh(),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showFormModal(),
        child: const Icon(Icons.add),
      ),
      body: Directionality(
        textDirection: TextDirection.rtl,
        child: state.isLoading
            ? const Center(child: CircularProgressIndicator())
            : state.rules.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.rule_folder, size: 64, color: Colors.grey),
                        const SizedBox(height: 16),
                        Text(state.error ?? 'قانونی تعریف نشده است'),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: state.rules.length,
                    itemBuilder: (context, index) {
                      final rule = state.rules[index];
                      return _ReportRuleCard(
                        rule: rule,
                        onEdit: () => _showFormModal(rule: rule),
                        onDelete: () => _confirmDelete(rule),
                        onTestRun: () async {
                          final messenger = ScaffoldMessenger.of(context);
                          await ref
                              .read(reportRulesProvider.notifier)
                              .testRun(rule.id);
                          if (mounted) {
                            messenger.showSnackBar(
                              const SnackBar(
                                content: Text('اجرای آزمایشی ارسال شد'),
                                backgroundColor: Colors.green,
                              ),
                            );
                          }
                        },
                      );
                    },
                  ),
      ),
    );
  }

  void _confirmDelete(ReportRule rule) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('حذف قانون'),
        content: Text('آیا از حذف «${rule.name}» مطمئن هستید؟'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('انصراف'),
          ),
          FilledButton(
            onPressed: () {
              ref.read(reportRulesProvider.notifier).deleteRule(rule.id);
              Navigator.pop(context);
            },
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('حذف'),
          ),
        ],
      ),
    );
  }
}

class _ReportRuleCard extends StatelessWidget {
  final ReportRule rule;
  final VoidCallback onEdit;
  final VoidCallback onDelete;
  final VoidCallback onTestRun;

  const _ReportRuleCard({
    required this.rule,
    required this.onEdit,
    required this.onDelete,
    required this.onTestRun,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    rule.name,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Switch(
                  value: rule.enabled,
                  onChanged: null,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                if (rule.zones.isNotEmpty)
                  Chip(
                    label: Text(rule.zones.join(', '),
                        style: const TextStyle(fontSize: 11)),
                    padding: EdgeInsets.zero,
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                Chip(
                  label: Text('${rule.intervalHours} ساعت',
                      style: const TextStyle(fontSize: 11)),
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                Chip(
                  label: Text(rule.destination == 'telegram' ? 'تلگرام' : 'بله',
                      style: const TextStyle(fontSize: 11)),
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ],
            ),
            if (rule.lastRun.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'آخرین اجرا: ${rule.lastRun} (${rule.lastStatus})',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
              ),
            ],
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton.icon(
                  onPressed: onTestRun,
                  icon: const Icon(Icons.play_arrow, size: 18),
                  label: const Text('اجرا'),
                ),
                TextButton.icon(
                  onPressed: onEdit,
                  icon: const Icon(Icons.edit, size: 18),
                  label: const Text('ویرایش'),
                ),
                TextButton.icon(
                  onPressed: onDelete,
                  icon: const Icon(Icons.delete, size: 18),
                  style: TextButton.styleFrom(foregroundColor: Colors.red),
                  label: const Text('حذف'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ReportRuleFormModal extends ConsumerStatefulWidget {
  final ReportRule? rule;
  final Future<void> Function(Map<String, dynamic> payload) onSubmit;

  const _ReportRuleFormModal({this.rule, required this.onSubmit});

  @override
  ConsumerState<_ReportRuleFormModal> createState() =>
      _ReportRuleFormModalState();
}

class _ReportRuleFormModalState extends ConsumerState<_ReportRuleFormModal> {
  late TextEditingController _nameController;
  late TextEditingController _intervalController;
  late TextEditingController _chatIdController;
  late TextEditingController _promptController;
  late TextEditingController _zonesController;
  late TextEditingController _camerasController;
  late TextEditingController _labelsController;
  String _destination = 'telegram';
  String _timezone = 'Asia/Tehran';
  bool _enabled = true;
  bool _includeSummary = true;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    final r = widget.rule;
    _nameController = TextEditingController(text: r?.name ?? '');
    _intervalController =
        TextEditingController(text: (r?.intervalHours ?? 24).toString());
    _chatIdController = TextEditingController(text: r?.chatId ?? '');
    _promptController = TextEditingController(text: r?.promptTemplate ?? '');
    _zonesController =
        TextEditingController(text: r?.zones.join(', ') ?? '');
    _camerasController =
        TextEditingController(text: r?.cameras.join(', ') ?? '');
    _labelsController =
        TextEditingController(text: r?.labels.join(', ') ?? '');
    _destination = r?.destination ?? 'telegram';
    _timezone = r?.timezone ?? 'Asia/Tehran';
    _enabled = r?.enabled ?? true;
    _includeSummary = r?.includeSummary ?? true;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _intervalController.dispose();
    _chatIdController.dispose();
    _promptController.dispose();
    _zonesController.dispose();
    _camerasController.dispose();
    _labelsController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final payload = <String, dynamic>{
      'name': _nameController.text.trim(),
      'enabled': _enabled,
      'zones': _zonesController.text
          .split(',')
          .map((s) => s.trim())
          .where((s) => s.isNotEmpty)
          .toList(),
      'cameras': _camerasController.text
          .split(',')
          .map((s) => s.trim())
          .where((s) => s.isNotEmpty)
          .toList(),
      'labels': _labelsController.text
          .split(',')
          .map((s) => s.trim())
          .where((s) => s.isNotEmpty)
          .toList(),
      'interval_hours': int.tryParse(_intervalController.text.trim()) ?? 24,
      'timezone': _timezone,
      'destination': _destination,
      'chat_id': _chatIdController.text.trim(),
      'prompt_template': _promptController.text.trim(),
      'include_summary': _includeSummary,
      'include_raw_data': false,
    };

    setState(() => _isSubmitting = true);
    try {
      await widget.onSubmit(payload);
    } catch (e) {
      debugPrint('[ReportRules] Form submit error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('خطا: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Padding(
        padding: EdgeInsets.only(
          left: 24,
          right: 24,
          top: 24,
          bottom: MediaQuery.of(context).viewInsets.bottom + 24,
        ),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                widget.rule == null ? 'افزودن قانون جدید' : 'ویرایش قانون',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 20),
              _Label('نام قانون'),
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              _Label('مناطق (با کاما جدا کنید)'),
              TextField(
                controller: _zonesController,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'ahmad_table, main_gate',
                ),
              ),
              const SizedBox(height: 16),
              _Label('دوربین‌ها'),
              TextField(
                controller: _camerasController,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'cam1',
                ),
              ),
              const SizedBox(height: 16),
              _Label('برچسب‌ها'),
              TextField(
                controller: _labelsController,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'person, car',
                ),
              ),
              const SizedBox(height: 16),
              _Label('بازه زمانی (ساعت)'),
              TextField(
                controller: _intervalController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              _Label('مقصد'),
              DropdownButtonFormField<String>(
                initialValue: _destination,
                decoration: const InputDecoration(border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'telegram', child: Text('تلگرام')),
                  DropdownMenuItem(value: 'bale', child: Text('بله')),
                  DropdownMenuItem(value: 'both', child: Text('هر دو')),
                ],
                onChanged: (v) => setState(() => _destination = v ?? 'telegram'),
              ),
              const SizedBox(height: 16),
              _Label('منطقه زمانی'),
              DropdownButtonFormField<String>(
                initialValue: _timezone,
                decoration: const InputDecoration(border: OutlineInputBorder()),
                items: [
                  'Asia/Tehran',
                  'UTC',
                  'Europe/London',
                  'America/New_York',
                  'Asia/Dubai',
                ]
                    .map((tz) =>
                        DropdownMenuItem(value: tz, child: Text(tz)))
                    .toList(),
                onChanged: (v) => setState(() => _timezone = v ?? 'Asia/Tehran'),
              ),
              const SizedBox(height: 16),
              _Label('Chat ID (اختیاری)'),
              TextField(
                controller: _chatIdController,
                decoration: const InputDecoration(border: OutlineInputBorder()),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
              _Label('قالب درخواست (اختیاری)'),
              TextField(
                controller: _promptController,
                maxLines: 3,
                decoration: const InputDecoration(border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              SwitchListTile(
                title: const Text('فعال'),
                value: _enabled,
                onChanged: (v) => setState(() => _enabled = v),
              ),
              SwitchListTile(
                title: const Text('شامل خلاصه هوش مصنوعی'),
                value: _includeSummary,
                onChanged: (v) => setState(() => _includeSummary = v),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: FilledButton(
                  onPressed: _isSubmitting ? null : _submit,
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(widget.rule == null ? 'ایجاد' : 'ذخیره'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Label extends StatelessWidget {
  final String text;
  const _Label(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(text, style: Theme.of(context).textTheme.labelLarge),
    );
  }
}
