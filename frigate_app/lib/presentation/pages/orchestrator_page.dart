import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/orchestrator_provider.dart';
import '../providers/server_config_provider.dart';

class OrchestratorPage extends ConsumerStatefulWidget {
  const OrchestratorPage({super.key});

  @override
  ConsumerState<OrchestratorPage> createState() => _OrchestratorPageState();
}

class _OrchestratorPageState extends ConsumerState<OrchestratorPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(orchestratorProvider.notifier).refreshAll();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(orchestratorProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('مدیریت سخت‌افزار و منابع'),
        centerTitle: true,
        actions: [
          IconButton(
            onPressed: () =>
                ref.read(orchestratorProvider.notifier).refreshAll(),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Directionality(
        textDirection: TextDirection.rtl,
        child: RefreshIndicator(
          onRefresh: () =>
              ref.read(orchestratorProvider.notifier).refreshAll(),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _HardwareSection(state: state),
              const SizedBox(height: 24),
              _ContainersSection(state: state),
            ],
          ),
        ),
      ),
    );
  }
}

class _HardwareSection extends StatelessWidget {
  final OrchestratorState state;

  const _HardwareSection({required this.state});

  @override
  Widget build(BuildContext context) {
    if (state.isLoadingHardware) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    final hw = state.hardware;
    if (hw == null) {
      return Card(
        child: ListTile(
          leading: const Icon(Icons.memory, color: Colors.grey),
          title: const Text('اطلاعات سخت‌افزار در دسترس نیست'),
          subtitle: state.error != null ? Text(state.error!) : null,
        ),
      );
    }

    final cpu = hw['cpu'] as Map<String, dynamic>? ?? {};
    final mem = hw['memory'] as Map<String, dynamic>? ?? {};
    final gpus = hw['gpus'] as List? ?? [];

    final cpuCores = cpu['cores'] ?? 0;
    final cpuUtil = (cpu['utilization_pct'] ?? 0.0).toDouble();
    final memTotal = (mem['total_gb'] ?? 0.0).toDouble();
    final memAvail = (mem['available_gb'] ?? 0.0).toDouble();
    final memUsedPct = (mem['used_pct'] ?? 0.0).toDouble();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.memory, size: 24),
                const SizedBox(width: 8),
                Text('منابع سخت‌افزاری',
                    style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const Divider(height: 24),
            _ResourceBar(
              icon: Icons.developer_board,
              label: 'CPU',
              valueText: '$cpuCores هسته • ${cpuUtil.toStringAsFixed(1)}%',
              progress: cpuUtil / 100,
              color: _utilColor(cpuUtil),
            ),
            const SizedBox(height: 16),
            _ResourceBar(
              icon: Icons.memory,
              label: 'حافظه RAM',
              valueText:
                  '${memAvail.toStringAsFixed(1)} / ${memTotal.toStringAsFixed(1)} گیگابایت آزاد',
              progress: memUsedPct / 100,
              color: _utilColor(memUsedPct),
            ),
            if (gpus.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Divider(),
              const SizedBox(height: 8),
              Text('کارت‌های گرافیک (${gpus.length})',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 12),
              ...gpus.map((g) => _GpuCard(gpu: g as Map<String, dynamic>)),
            ],
          ],
        ),
      ),
    );
  }

  Color _utilColor(double pct) {
    if (pct < 50) return Colors.green;
    if (pct < 80) return Colors.orange;
    return Colors.red;
  }
}

class _ResourceBar extends StatelessWidget {
  final IconData icon;
  final String label;
  final String valueText;
  final double progress;
  final Color color;

  const _ResourceBar({
    required this.icon,
    required this.label,
    required this.valueText,
    required this.progress,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 18, color: Colors.grey),
            const SizedBox(width: 6),
            Text(label, style: Theme.of(context).textTheme.bodyMedium),
            const Spacer(),
            Text(valueText,
                style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: progress.clamp(0.0, 1.0),
            minHeight: 8,
            backgroundColor: Colors.grey.shade800,
            color: color,
          ),
        ),
      ],
    );
  }
}

class _GpuCard extends StatelessWidget {
  final Map<String, dynamic> gpu;

  const _GpuCard({required this.gpu});

  @override
  Widget build(BuildContext context) {
    final name = gpu['name'] ?? 'Unknown GPU';
    final gpuIndex = gpu['index'] ?? 0;
    final memTotal = (gpu['memory_total_mb'] ?? 0).toInt();
    final memUsed = (gpu['memory_used_mb'] ?? 0).toInt();
    final util = (gpu['gpu_utilization_pct'] ?? 0.0).toDouble();
    final memPct = memTotal > 0 ? memUsed / memTotal : 0.0;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.grey.shade900,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey.shade700),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.videogame_asset, size: 18),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(name,
                      style: Theme.of(context).textTheme.bodyMedium),
                ),
                Text('#$gpuIndex',
                    style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
            const SizedBox(height: 12),
            _ResourceBar(
              icon: Icons.speed,
              label: 'محاسبه GPU',
              valueText: '${util.toStringAsFixed(1)}%',
              progress: util / 100,
              color: util < 50 ? Colors.green : (util < 80 ? Colors.orange : Colors.red),
            ),
            const SizedBox(height: 10),
            _ResourceBar(
              icon: Icons.storage,
              label: 'حافظه GPU',
              valueText: '$memUsed / $memTotal مگابایت',
              progress: memPct,
              color: memPct < 0.5 ? Colors.green : (memPct < 0.8 ? Colors.orange : Colors.red),
            ),
          ],
        ),
      ),
    );
  }
}

class _ContainersSection extends StatelessWidget {
  final OrchestratorState state;

  const _ContainersSection({required this.state});

  @override
  Widget build(BuildContext context) {
    if (state.isLoadingContainers) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    final containers = state.containers;
    if (containers.isEmpty) {
      return Card(
        child: ListTile(
          leading: const Icon(Icons.dns, color: Colors.grey),
          title: const Text('کانتینری یافت نشد'),
          subtitle: state.error != null ? Text(state.error!) : null,
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.dns, size: 24),
                const SizedBox(width: 8),
                Text('کانتینرهای فعال (${containers.length})',
                    style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const Divider(height: 24),
            ...containers.map((c) => _ContainerTile(container: c as Map<String, dynamic>)),
          ],
        ),
      ),
    );
  }
}

class _ContainerTile extends ConsumerStatefulWidget {
  final Map<String, dynamic> container;

  const _ContainerTile({required this.container});

  @override
  ConsumerState<_ContainerTile> createState() => _ContainerTileState();
}

class _ContainerTileState extends ConsumerState<_ContainerTile> {
  late TextEditingController _memoryController;
  final Set<int> _selectedCores = {};
  String? _selectedGpu;
  bool _isApplying = false;

  @override
  void initState() {
    super.initState();
    _memoryController = TextEditingController(text: '4');
  }

  @override
  void dispose() {
    _memoryController.dispose();
    super.dispose();
  }

  bool get _supportsGpu {
    final cap = widget.container['capability'] as Map<String, dynamic>?;
    return cap?['supports_gpu'] as bool? ?? false;
  }

  String get _detectionStrategy {
    final cap = widget.container['capability'] as Map<String, dynamic>?;
    return cap?['detection_strategy'] as String? ?? 'cpu_only';
  }

  Future<void> _applyAssignment() async {
    final name = widget.container['name'] ?? 'unknown';
    setState(() => _isApplying = true);
    try {
      final client = ref.read(apiClientProvider);
      await client.assignResources({
        'container': name,
        'cpu_cores': _selectedCores.toList()..sort(),
        'gpu': _supportsGpu && _selectedGpu != null ? _selectedGpu : null,
        'memory_limit_gb': int.tryParse(_memoryController.text.trim()) ?? 4,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('منابع $name اعمال شد'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      debugPrint('[Orchestrator] Failed to assign resources: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('خطا در اعمال منابع: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isApplying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final name = widget.container['name'] ?? 'unknown';
    final image = widget.container['image'] ?? '';
    final status = widget.container['status'] ?? 'unknown';
    final shortId = widget.container['short_id'] ?? '';
    final ports = widget.container['ports'] as List? ?? [];
    final hw = ref.watch(orchestratorProvider).hardware;
    final cpuCores = (hw?['cpu']?['cores'] ?? 8) as int;
    final gpus = (hw?['gpus'] as List? ?? []);

    final isRunning = status == 'running';

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.grey.shade900,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade700),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isRunning ? Colors.green : Colors.red,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(name, style: Theme.of(context).textTheme.bodyMedium),
                      const SizedBox(height: 2),
                      Text(
                        '$image • $status • $shortId',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.grey,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (ports.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Wrap(
                  spacing: 6,
                  children: ports.map((p) {
                    final port = p as Map<String, dynamic>;
                    final hostPort = port['host_port'] ?? '';
                    final containerPort = port['container_port'] ?? '';
                    return Chip(
                      label: Text(
                        '$hostPort → $containerPort',
                        style: const TextStyle(fontSize: 10),
                      ),
                      padding: EdgeInsets.zero,
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    );
                  }).toList(),
                ),
              ),
            const Divider(height: 24),
            Text('هسته‌های CPU',
                style: Theme.of(context).textTheme.labelMedium),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: List.generate(cpuCores, (i) {
                final isSelected = _selectedCores.contains(i);
                return FilterChip(
                  label: Text('${i + 1}'),
                  selected: isSelected,
                  onSelected: (selected) {
                    setState(() {
                      if (selected) {
                        _selectedCores.add(i);
                      } else {
                        _selectedCores.remove(i);
                      }
                    });
                  },
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                );
              }),
            ),
            const SizedBox(height: 16),
            Text('کارت گرافیک',
                style: Theme.of(context).textTheme.labelMedium),
            const SizedBox(height: 8),
            if (_supportsGpu)
              DropdownButtonFormField<String>(
                initialValue: _selectedGpu,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
                hint: const Text('انتخاب GPU'),
                items: [
                  const DropdownMenuItem(value: null, child: Text('بدون GPU')),
                  ...gpus.map((g) {
                    final gpu = g as Map<String, dynamic>;
                    return DropdownMenuItem(
                      value: 'gpu-${gpu['index'] ?? 0}',
                      child: Text(gpu['name'] ?? 'GPU #${gpu['index']}'),
                    );
                  }),
                ],
                onChanged: (v) => setState(() => _selectedGpu = v),
              )
            else
              Tooltip(
                message: 'این کانتینر از GPU پشتیبانی نمی‌کند ($_detectionStrategy)',
                child: DropdownButtonFormField<String>(
                  initialValue: null,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    isDense: true,
                    prefixIcon: Icon(Icons.warning, color: Colors.orange),
                  ),
                  hint: const Text('GPU پشتیبانی نمی‌شود'),
                  items: const [],
                  onChanged: null,
                ),
              ),
            const SizedBox(height: 16),
            Text('محدودیت حافظه (GB)',
                style: Theme.of(context).textTheme.labelMedium),
            const SizedBox(height: 8),
            TextField(
              controller: _memoryController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              height: 40,
              child: FilledButton.icon(
                onPressed: _isApplying ? null : _applyAssignment,
                icon: _isApplying
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.check, size: 18),
                label: const Text('اعمال'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
