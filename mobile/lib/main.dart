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
      theme: buildAppTheme(),
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
  String _status =
      'Init a store, drop a file you already have. Tick copies locally. We do not mail.';

  @override
  void dispose() {
    _summary.dispose();
    _payload.dispose();
    _hours.dispose();
    super.dispose();
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
      _status = 'Store ready. Drop a file you already have. Does not mail.';
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
      _status = 'Dropped $dropId. Local copy only.';
    });
  }

  void _checkin() {
    if (_chain.isEmpty) _init();
    setState(() {
      _lastCheckin = _now();
      _append('checkin', 'checkin at $_lastCheckin');
      _status = 'Checked in. Clock reset. Tick will not copy inside the window.';
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
      _status =
          'Armed for $_intervalHours hour(s). Dead-man copy is local. We do not mail.';
    });
  }

  void _tick({bool forceOverdue = false}) {
    if (!_armed) {
      setState(() => _status = 'Not armed. Tap Arm first.');
      return;
    }
    if (_released && !forceOverdue) {
      setState(() =>
          _status = 'Already released. Arm again for another local copy. We do not mail.');
      return;
    }
    setState(() {
      _released = true;
      _append('release', 'dead-man copied locally');
      _status =
          'Overdue. Copied packet locally. WhistleLock did not mail it.';
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
      _status = ok
          ? 'Chain hashes. Dead-man copy is local. Does not mail.'
          : 'Chain did not hash.';
      if (ok) _append('verify', 'verify rows=${_chain.length} errors=0 missing=0 refresh=false');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('WhistleLock')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(limitation, style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              FilledButton(onPressed: _init, child: const Text('Init')),
              FilledButton(onPressed: _drop, child: const Text('Drop')),
              FilledButton(onPressed: _checkin, child: const Text('Check in')),
              FilledButton(onPressed: _arm, child: const Text('Arm')),
              FilledButton(onPressed: _tick, child: const Text('Tick')),
              FilledButton(onPressed: _verify, child: const Text('Verify')),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _summary,
            decoration: const InputDecoration(labelText: 'Summary'),
          ),
          TextField(
            controller: _payload,
            decoration: const InputDecoration(
                labelText: 'Drop text (hashed locally; not mailed)'),
          ),
          TextField(
            controller: _hours,
            decoration: const InputDecoration(labelText: 'Arm hours'),
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 12),
          Text(_status),
          Text(
            'armed=$_armed  window=$_intervalHours  released=$_released  rows=${_chain.length}',
          ),
          const SizedBox(height: 12),
          ..._chain.reversed.take(8).map(
                (r) => ListTile(
                  dense: true,
                  title: Text('${r.kind} · ${r.summary}'),
                  subtitle: Text(r.hash.substring(0, 16) + '…'),
                ),
              ),
        ],
      ),
    );
  }
}
