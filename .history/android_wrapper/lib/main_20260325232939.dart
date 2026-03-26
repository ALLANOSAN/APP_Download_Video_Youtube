import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

const String backendUrl = 'https://app-download-video-youtube.fly.dev';

void main() {
  runApp(const MyApp());
}

class ApiClient {
  final String baseUrl;
  const ApiClient({this.baseUrl = backendUrl});

  Future<String> root() async {
    final r = await http.get(Uri.parse('$baseUrl/'));
    if (r.statusCode == 200) {
      final data = jsonDecode(r.body);
      return 'API: ${data['message'] ?? data}';
    }
    throw Exception('Erro / ${r.statusCode}: ${r.body}');
  }

  Future<String> register(String username, String email, String password) async {
    final r = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
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
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: 'username=$username&password=$password',
    );
    if (r.statusCode == 200) {
      return 'Login OK';
    }
    return 'Falha login: ${r.statusCode} ${r.body}';
  }

  Future<String> history() async {
    final r = await http.get(Uri.parse('$baseUrl/history'));
    if (r.statusCode == 200) {
      return r.body;
    }
    return 'Falha history: ${r.statusCode} ${r.body}';
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
  final ApiClient _api = const ApiClient();
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
                        final t = await _api.register(
                            _username.text.trim(),
                            _email.text.trim(),
                            _password.text.trim());
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
              const SizedBox(height: 20),
              Text('Status: $_status', style: const TextStyle(fontSize: 16)),
            ],
          ),
        ),
      ),
    );
  }
}
