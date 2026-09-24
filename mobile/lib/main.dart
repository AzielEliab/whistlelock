import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';

import 'theme.dart';

const genesisPrev =
    '0000000000000000000000000000000000000000000000000000000000000000';
const limitation =
    'THIS IS a local drop ledger + local dead-man copy. '
    'THIS IS NOT a mailer, mixnet, IP mask, inbox scraper, FoldLock, or GodLock. '
    'Hosted never holds whistle files. Demo drops are generic (sample drop).';

void main() {
  runApp(const WhistleLockApp());
}

class WhistleLockApp extends StatelessWidget {
  const WhistleLockApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WhistleLock',
      debugShowCheckedModeBanner: false,
      theme: buildLightTheme(),
      darkTheme: buildDarkTheme(),
      themeMode: ThemeMode.system,
      home: const VaultPage(),
    );
  }
}

class LedgerRow {
  LedgerRow({
    required this.entryId,
    required this.timestamp,
    required this.kind,
    required this.summary,
    required this.dropId,
    required this.payloadSha256,
    required this.sourceNote,
    required this.prevHash,
    required this.hash,
  });

  final String entryId;
  final String timestamp;
  final String kind;
  final String summary;
  final String dropId;
  final String payloadSha256;
  final String sourceNote;
  final String prevHash;
  final String hash;

  bool get hashOk => recompute() == hash;

  String recompute() => digest({
        'drop_id': dropId,
        'entry_id': entryId,
        'kind': kind,
        'payload_sha256': payloadSha256,
        'prev_hash': prevHash,
        'source_note': sourceNote,
        'summary': summary,
        'timestamp': timestamp,
      });
}

String digest(Map<String, String> fields) {
  final keys = fields.keys.toList()..sort();
  final raw =
      '{${keys.map((k) => '${jsonEncode(k)}:${jsonEncode(fields[k])}').join(',')}}';
  return sha256.convert(utf8.encode(raw)).toString();
}

class VaultPage extends StatefulWidget {
  const VaultPage({super.key});

  @override
  State<VaultPage> createState() => _VaultPageState();
}

class _VaultPageState extends State<VaultPage> {
  final _summary = TextEditingController(text: 'sample drop');
  final _payload = TextEditingController(text: 'sample drop');
  final _hours = TextEditingController(text: '1');
  final _chain = <LedgerRow>[];
  bool _armed = false;
  bool _released = false;
  String _lastCheckin = '';
  int _intervalHours = 0;
  String _status = 'Drop text you already have.';

  @override
  void dispose() {
    _summary.dispose();
    _payload.dispose();
    _hours.dispose();
    super.dispose();
  }

  String get _clockLine {
    if (!_armed) return 'Check-in clock is not armed.';
    if (_released) return 'A local copy was already made.';
    return 'Armed for $_intervalHours hour(s). Rows: ${_chain.length}.';
  }

  String _now() =>
      DateTime.now().toUtc().toIso8601String().split('.').first + 'Z';

  void _append(String kind, String summary,
      {String dropId = '', String payload = '', String source = ''}) {
    final prev = _chain.isEmpty ? genesisPrev : _chain.last.hash;
    final n = _chain.length + 1;
    final entryId = 'WL-${n.toString().padLeft(4, '0')}';
    final ts = _now();
    final fields = <String, String>{
      'entry_id': entryId,
      'timestamp': ts,
      'kind': kind,
      'summary': summary,
      'drop_id': dropId,
      'payload_sha256': payload,
      'source_note': source,
      'prev_hash': prev,
    };
    _chain.add(LedgerRow(
      entryId: entryId,
      timestamp: ts,
      kind: kind,
      summary: summary,
      dropId: dropId,
      payloadSha256: payload,
      sourceNote: source,
      prevHash: prev,
      hash: digest(fields),
    ));
  }

  void _init() {
    setState(() {
      _chain.clear();
      _armed = false;
      _released = false;
      _lastCheckin = '';
      _intervalHours = 0;
      _append('note', 'store genesis');
      _status = 'Store ready. Drop text you already have.';
    });
  }

  void _drop() {
    if (_chain.isEmpty) _init();
    final bytes = utf8.encode(_payload.text);
    final payload = sha256.convert(bytes).toString();
    final dropId = 'DR-${payload.substring(0, 12)}';
    setState(() {
      _append('drop', _summary.text.isEmpty ? 'sample drop' : _summary.text,
          dropId: dropId, payload: payload);
      _status = 'Dropped $dropId.';
    });
  }

  void _checkin() {
    if (_chain.isEmpty) _init();
    setState(() {
      _lastCheckin = _now();
      _append('checkin', 'checkin at $_lastCheckin');
      _status = 'Checked in. The clock reset.';
    });
  }

  void _arm() {
    if (_chain.isEmpty) _init();
    final hours = int.tryParse(_hours.text) ?? 1;
    setState(() {
      _armed = true;
      _released = false;
      _intervalHours = hours < 1 ? 1 : hours;
      _lastCheckin = _now();
      _append('arm', 'armed $_intervalHours h');
      _status = 'Armed for $_intervalHours hour(s). Check in before then.';
    });
  }

  void _tick({bool forceOverdue = false}) {
    if (!_armed) {
      setState(() => _status = 'Not armed yet. Open Advanced and tap Arm.');
      return;
    }
    if (_released && !forceOverdue) {
      setState(() =>
          _status = 'Already copied. Open Advanced and tap Arm for another local copy.');
      return;
    }
    setState(() {
      _released = true;
      _append('release', 'dead-man copied locally');
      _status = 'Copied the packet on this device. It was not mailed.';
    });
  }

  void _verify() {
    var expected = genesisPrev;
    var ok = true;
    for (final row in _chain) {
      if (row.prevHash != expected || !row.hashOk) {
        ok = false;
        break;
      }
      expected = row.hash;
    }
    setState(() {
      _status = ok ? 'Chain checks out.' : 'The chain needs a look.';
      if (ok) _append('verify', 'verify rows=${_chain.length} errors=0 missing=0 refresh=false');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('WhistleLock')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Keep a local ledger of text you already have. If you miss a check-in, a packet is copied on this device.',
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 16),
          Text(_status, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 16),
          FilledButton(onPressed: _drop, child: const Text('Drop')),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(onPressed: _checkin, child: const Text('Check in')),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton(onPressed: _verify, child: const Text('Verify')),
              ),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _summary,
            decoration: const InputDecoration(labelText: 'Summary'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _payload,
            decoration: const InputDecoration(labelText: 'Drop text'),
          ),
          const SizedBox(height: 8),
          ExpansionTile(
            title: const Text('Advanced'),
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    OutlinedButton(onPressed: _init, child: const Text('Init')),
                    OutlinedButton(onPressed: _arm, child: const Text('Arm')),
                    OutlinedButton(onPressed: _tick, child: const Text('Tick')),
                  ],
                ),
              ),
              TextField(
                controller: _hours,
                decoration: const InputDecoration(labelText: 'Hours before a local copy'),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(_clockLine),
              ),
            ],
          ),
          ExpansionTile(
            title: const Text('About'),
            children: [
              Text(limitation),
              const SizedBox(height: 8),
              const Text('Author: Aziel Eliab. Apache-2.0.'),
            ],
          ),
          const SizedBox(height: 8),
          ..._chain.reversed.take(8).map(
                (r) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text('${r.kind} · ${r.summary}'),
                  subtitle: Text('${r.hash.substring(0, 16)}…'),
                ),
              ),
        ],
      ),
    );
  }
}
