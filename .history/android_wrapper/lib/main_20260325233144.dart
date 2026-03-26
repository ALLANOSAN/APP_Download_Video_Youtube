import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const String backendUrl = 'https://app-download-video-youtube.fly.dev';

void main() {
  runApp(const MyApp());
}

class ApiClient {
  final String baseUrl;
  String? _token;

  ApiClient({this.baseUrl = backendUrl});

  Map<String, String> get _jsonHeaders => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Map<String, String> get _formHeaders => {
        'Content-Type': 'application/x-www-form-urlencoded',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  Future<String> root() async {
    final r = await http.get(Uri.parse('$baseUrl/'), headers: _jsonHeaders);
    if (r.statusCode == 200) {
      final data = jsonDecode(r.body);
      return 'API: ${data['message'] ?? data}';
    }
    throw Exception('Erro / ${r.statusCode}: ${r.body}');
  }

  Future<String> register(
      String username, String email, String password) async {
    final r = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: _jsonHeaders,
      body: jsonEncode({
        'username': username,
        'email': email,
        'password': password,
      }),
    );
    if (r.statusCode == 201 || r.statusCode == 200)
      return 'Usuário criado com sucesso';
    return 'Falha registrando: ${r.statusCode} ${r.body}';
  }

  Future<String> login(String username, String password) async {
    final r = await http.post(
      Uri.parse('$baseUrl/auth/token'),
      headers: _formHeaders,
      body: 'username=$username&password=$password',
    );
    if (r.statusCode == 200) {
      final data = jsonDecode(r.body);
      _token = data['access_token'];
      return 'Login OK';
    }
    return 'Falha login: ${r.statusCode} ${r.body}';
  }

  Future<String> history() async {
    final r =
        await http.get(Uri.parse('$baseUrl/history'), headers: _jsonHeaders);
    if (r.statusCode == 200) {
      return r.body;
    }
    return 'Falha history: ${r.statusCode} ${r.body}';
  }

  Future<String> addHistory(Map<String, dynamic> item) async {
    final r = await http.post(
      Uri.parse('$baseUrl/history'),
      headers: _jsonHeaders,
      body: jsonEncode(item),
    );

    if (r.statusCode == 201 || r.statusCode == 200) {
      return 'Item salvo';
    }
    return 'Falha add history: ${r.statusCode} ${r.body}';
  }

  Future<String> download(String url, String mode, String audioFormat,
      String audioQuality, String videoQuality) async {
    final r = await http.post(
      Uri.parse('$baseUrl/download'),
      headers: _jsonHeaders,
      body: jsonEncode({
        'url': url,
        'mode': mode,
        'audio_format': audioFormat,
        'audio_quality': audioQuality,
        'video_quality': videoQuality,
      }),
    );
    if (r.statusCode == 200) {
      final data = jsonDecode(r.body);
      return data['task_id'] ?? 'download started';
    }
    return 'Falha download: ${r.statusCode} ${r.body}';
  }

  Future<String> downloadProgress(String taskId) async {
    final r = await http.get(Uri.parse('$baseUrl/download_progress/$taskId'),
        headers: _jsonHeaders);
    if (r.statusCode == 200) {
      return r.body;
    }
    return 'Falha progress: ${r.statusCode} ${r.body}';
  }

  Future<String> cancelDownload(String taskId) async {
    final r = await http.delete(Uri.parse('$baseUrl/download_task/$taskId'),
        headers: _jsonHeaders);
    if (r.statusCode == 200) {
      return r.body;
    }
    return 'Falha cancelar: ${r.statusCode} ${r.body}';
  }

  Future<String> registerFcmToken(String userId, String fcmToken) async {
    final r = await http.post(
      Uri.parse('$baseUrl/fcm/register_token'),
      headers: _jsonHeaders,
      body: jsonEncode({'user_id': userId, 'fcm_token': fcmToken}),
    );
    if (r.statusCode == 200) {
      return 'FCM token registrado';
    }
    return 'Falha FCM register: ${r.statusCode} ${r.body}';
  }

  Future<String> sendFcm(String userId, String title, String body) async {
    final r = await http.post(
      Uri.parse('$baseUrl/fcm/send'),
      headers: _jsonHeaders,
      body: jsonEncode(
          {'user_id': userId, 'title': title, 'body': body, 'data': {}}),
    );
    if (r.statusCode == 200) {
      return 'FCM send OK';
    }
    return 'Falha FCM send: ${r.statusCode} ${r.body}';
  }
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  final TextEditingController _username = TextEditingController();
  final TextEditingController _email = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _downloadUrl = TextEditingController();
  final TextEditingController _taskId = TextEditingController();
  String _downloadMode = 'audio';
  String _status = 'Pronto';

  Future<void> _setStatus(String s) async {
    setState(() {
      _status = s;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'YouTube Downloader Client',
      home: Scaffold(
        appBar: AppBar(title: const Text('YouTube Downloader Client')),
        body: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Text('Backend: $backendUrl'),
              const SizedBox(height: 16),
              TextField(
                  controller: _username,
                  decoration: const InputDecoration(labelText: 'Usuário')),
              const SizedBox(height: 8),
              TextField(
                  controller: _email,
                  decoration: const InputDecoration(labelText: 'Email')),
              const SizedBox(height: 8),
              TextField(
                  controller: _password,
                  decoration: const InputDecoration(labelText: 'Senha'),
                  obscureText: true),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () async {
                        await _setStatus('Registrando...');
                        final t = await _api.register(_username.text.trim(),
                            _email.text.trim(), _password.text.trim());
                        await _setStatus(t);
                      },
                      child: const Text('Registrar'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () async {
                        await _setStatus('Login...');
                        final t = await _api.login(
                            _username.text.trim(), _password.text.trim());
                        await _setStatus(t);
                      },
                      child: const Text('Login'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () async {
                  await _setStatus('Buscando / ...');
                  final t = await _api.root();
                  await _setStatus(t);
                },
                child: const Text('GET /'),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () async {
                  await _setStatus('Buscando /history ...');
                  final t = await _api.history();
                  await _setStatus(t);
                },
                child: const Text('GET /history'),
              ),
              const SizedBox(height: 12),
              const Divider(),
              const SizedBox(height: 12),
              TextField(
                controller: _downloadUrl,
                decoration:
                    const InputDecoration(labelText: 'URL para download'),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: _downloadMode,
                items: const [
                  DropdownMenuItem(value: 'audio', child: Text('Audio')),
                  DropdownMenuItem(value: 'video', child: Text('Video')),
                ],
                onChanged: (v) {
                  if (v != null) {
                    setState(() {
                      _downloadMode = v;
                    });
                  }
                },
                decoration: const InputDecoration(labelText: 'Modo'),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                  onPressed: () async {
                    await _setStatus('Iniciando download...');
                    final t = await _api.download(
                      _downloadUrl.text.trim(),
                      _downloadMode,
                      'mp3',
                      '192k',
                      '720p',
                    );
                    setState(() {
                      _taskId.text = t;
                    });
                    await _setStatus('Task criada: $t');
                  },
                  child: const Text('Iniciar download (POST /download)')),
              const SizedBox(height: 8),
              TextField(
                controller: _taskId,
                decoration: const InputDecoration(
                    labelText: 'Task ID para progress / cancel'),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () async {
                  final id = _taskId.text.trim();
                  if (id.isEmpty) {
                    await _setStatus('Informe task id para progress');
                    return;
                  }
                  final t = await _api.downloadProgress(id);
                  await _setStatus('Progress: $t');
                },
                child: const Text('GET /download_progress'),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () async {
                  final id = _taskId.text.trim();
                  if (id.isEmpty) {
                    await _setStatus('Informe task id para cancel');
                    return;
                  }
                  final t = await _api.cancelDownload(id);
                  await _setStatus('Cancelado: $t');
                },
                child: const Text('DELETE /download_task'),
              ),
              const SizedBox(height: 20),
              Text('Status: $_status', style: const TextStyle(fontSize: 16)),
            ],
          ),
        ),
      ),
    );
  }
}
