import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;

const String backendUrl = 'https://app-download-video-youtube.fly.dev';

class NotificationService {
  static final _localNotifications = FlutterLocalNotificationsPlugin();

  static Future<void> init() async {
    const settings = AndroidInitializationSettings('@mipmap/ic_launcher');
    await _localNotifications.initialize(
      settings: const InitializationSettings(android: settings),
      onDidReceiveNotificationResponse: (response) {
        // Opcional: lidar com ação de notificação quando o usuário clica.
      },
    );
  }

  static Future<void> show(String title, String body) async {
    const androidDetails = AndroidNotificationDetails(
      'channel_id',
      'Notifications',
      channelDescription: 'App notifications',
      importance: Importance.high,
      priority: Priority.high,
    );
    await _localNotifications.show(
      id: 0,
      title: title,
      body: body,
      notificationDetails: const NotificationDetails(android: androidDetails),
      payload: '',
    );
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService.init();
  runApp(const MyApp());
}

class ApiClient {
  final String baseUrl;
  String? _token;

  ApiClient({this.baseUrl = backendUrl});

  String? get token => _token;

  bool get isAuthenticated => _token != null;

  void logout() {
    _token = null;
  }

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

  bool _handleUnauthorized(http.Response r) {
    if (r.statusCode == 401) {
      logout();
      return true;
    }
    return false;
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
    if (_handleUnauthorized(r)) return 'Unauthorized - faça login novamente';
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
    if (_handleUnauthorized(r)) return 'Unauthorized - faça login novamente';
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

    if (_handleUnauthorized(r)) return 'Unauthorized - faça login novamente';
    if (r.statusCode == 201 || r.statusCode == 200) {
      return 'Item salvo';
    }
    return 'Falha add history: ${r.statusCode} ${r.body}';
  }

  Future<String> download({
    required String url,
    required String mode,
    required String format,
    required String quality,
  }) async {
    final r = await http.post(
      Uri.parse('$baseUrl/download'),
      headers: _jsonHeaders,
      body: jsonEncode({
        'url': url,
        'mode': mode,
        'audio_format': mode == 'audio' ? format : 'mp3',
        'audio_quality': mode == 'audio' ? quality : '192k',
        'video_quality': mode == 'video' ? quality : '720p',
      }),
    );
    if (_handleUnauthorized(r)) return 'Unauthorized - faça login novamente';
    if (r.statusCode != 200) {
      throw Exception('Falha no servidor: ${r.statusCode} ${r.body}');
    }
    final data = jsonDecode(r.body);
    final taskId = data['task_id'];
    if (taskId == null) throw Exception('Task ID não recebido');
    return taskId.toString();
  }

  Future<Map<String, dynamic>?> getVideoInfo(String url) async {
    try {
      final r = await http.get(
          Uri.parse('$baseUrl/video_info?url=${Uri.encodeComponent(url)}'),
          headers: _jsonHeaders);
      if (r.statusCode == 200) return jsonDecode(r.body);
    } catch (_) {}
    return null;
  }

  Future<String> downloadProgress(String taskId) async {
    final r = await http.get(Uri.parse('$baseUrl/download_progress/$taskId'),
        headers: _jsonHeaders);
    if (_handleUnauthorized(r)) return 'Unauthorized - faça login novamente';
    if (r.statusCode == 200) {
      return r.body;
    }
    return 'Falha progress: ${r.statusCode} ${r.body}';
  }

  Future<String> cancelDownload(String taskId) async {
    final r = await http.delete(Uri.parse('$baseUrl/download_task/$taskId'),
        headers: _jsonHeaders);
    if (_handleUnauthorized(r)) return 'Unauthorized - faça login novamente';
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
    if (_handleUnauthorized(r)) return 'Unauthorized - faça login novamente';
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
    if (_handleUnauthorized(r)) return 'Unauthorized - faça login novamente';
    if (r.statusCode == 200) {
      return 'FCM send OK';
    }
    return 'Falha FCM send: ${r.statusCode} ${r.body}';
  }

  Future<Uint8List> downloadFile(String taskId) async {
    final r = await http.get(Uri.parse('$baseUrl/download_file/$taskId'),
        headers: _jsonHeaders);
    if (_handleUnauthorized(r))
      throw Exception('Unauthorized - faça login novamente');
    if (r.statusCode == 200) {
      return r.bodyBytes;
    }
    throw Exception('Falha download_file: ${r.statusCode} ${r.body}');
  }
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  final GlobalKey<ScaffoldMessengerState> _scaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();
  final TextEditingController _username = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _downloadUrl = TextEditingController();
  final TextEditingController _taskId = TextEditingController();
  final ApiClient _api = ApiClient();
  String _downloadMode = 'audio';
  String _downloadFormat = 'mp3';
  String _downloadQuality = '192k';
  String _status = 'Pronto';
  List<Map<String, dynamic>> _historyItems = [];
  bool _isLoading = false;

  bool get _isLoggedIn => _api.isAuthenticated;

  Future<void> _setStatus(String s) async {
    setState(() {
      _status = s;
    });
  }

  Future<void> _loadHistory() async {
    try {
      final response = await _api.history();
      if (response.startsWith('Unauthorized')) {
        await _setStatus(response);
        return;
      }
      final parsed = jsonDecode(response);
      if (parsed is List) {
        setState(() {
          _historyItems = List<Map<String, dynamic>>.from(parsed);
        });
      } else {
        setState(() {
          _historyItems = [];
        });
      }
      await _setStatus('Histórico carregado: ${_historyItems.length} itens');
    } catch (e) {
      await _setStatus('Erro ao obter histórico: $e');
    }
  }

  void _startPolling(String taskId) {
    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 3));
      if (!mounted || !_api.isAuthenticated) return false;

      try {
        final res = await _api.downloadProgress(taskId);
        // Se o servidor retornar o status em texto ou JSON, tratamos aqui
        await _setStatus('Status: $res');

        if (res.toLowerCase().contains('concluído') ||
            res.toLowerCase().contains('finished') ||
            res.toLowerCase().contains('100%')) {
          await NotificationService.show(
              'Sucesso', 'Download concluído no servidor!');
          return false; // Para o loop
        }
        if (res.toLowerCase().contains('erro') ||
            res.toLowerCase().contains('fail')) return false;
      } catch (e) {
        return false;
      }
      return true; // Continua tentando
    });
  }

  void _logout() {
    _api.logout();
    setState(() {
      _historyItems = [];
      _status = 'Deslogado';
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'YouTube Downloader Client',
      home: Scaffold(
        resizeToAvoidBottomInset: true,
        appBar: AppBar(title: const Text('YouTube Downloader Client')),
        body: SingleChildScrollView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Backend: $backendUrl',
                    style: const TextStyle(fontSize: 14)),
                const SizedBox(height: 24),

                // Login / Register section
                TextField(
                  controller: _username,
                  decoration: const InputDecoration(
                    labelText: 'Usuário',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _password,
                  decoration: const InputDecoration(
                    labelText: 'Senha',
                    border: OutlineInputBorder(),
                  ),
                  obscureText: true,
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () async {
                          setState(() => _isLoading = true);
                          await _setStatus('Registrando...');
                          try {
                            final t = await _api.register(
                              _username.text.trim(),
                              '',
                              _password.text.trim(),
                            );
                            await _setStatus(t);
                          } catch (e) {
                            await _setStatus('Erro: $e');
                          } finally {
                            setState(() => _isLoading = false);
                          }
                        },
                        child: const Text('Registrar'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () async {
                          setState(() => _isLoading = true);
                          await _setStatus('Fazendo login...');
                          try {
                            final t = await _api.login(
                                _username.text.trim(), _password.text.trim());
                            await _setStatus(t);
                            if (t == 'Login OK') {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                    content: Text('Login realizado!')),
                              );
                              await NotificationService.show(
                                  'Login', 'Autenticado com sucesso');
                              await _loadHistory();
                            }
                          } catch (e) {
                            await _setStatus('Erro: $e');
                          } finally {
                            setState(() => _isLoading = false);
                          }
                        },
                        child: const Text('Login'),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 24),
                if (_isLoading)
                  const Center(child: CircularProgressIndicator()),

                if (_isLoggedIn) ...[
                  const Divider(),
                  const SizedBox(height: 16),
                  const Text('Download de vídeo/audio',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _downloadUrl,
                    decoration: const InputDecoration(
                      labelText: 'URL do YouTube',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: _downloadMode,
                    items: const [
                      DropdownMenuItem(value: 'audio', child: Text('Áudio')),
                      DropdownMenuItem(value: 'video', child: Text('Vídeo')),
                    ],
                    onChanged: (value) {
                      if (value != null) {
                        setState(() {
                          _downloadMode = value;
                          _downloadFormat = value == 'audio' ? 'mp3' : 'mp4';
                          _downloadQuality = value == 'audio' ? '192k' : '720p';
                        });
                      }
                    },
                    decoration: const InputDecoration(
                      labelText: 'Modo',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: _downloadFormat,
                    items: _downloadMode == 'audio'
                        ? const [
                            DropdownMenuItem(value: 'mp3', child: Text('MP3')),
                            DropdownMenuItem(value: 'm4a', child: Text('M4A')),
                            DropdownMenuItem(value: 'wav', child: Text('WAV')),
                            DropdownMenuItem(
                                value: 'flac', child: Text('FLAC')),
                            DropdownMenuItem(
                                value: 'opus', child: Text('OPUS')),
                            DropdownMenuItem(value: 'aac', child: Text('AAC')),
                            DropdownMenuItem(value: 'ogg', child: Text('OGG')),
                          ]
                        : const [
                            DropdownMenuItem(value: 'mp4', child: Text('MP4')),
                            DropdownMenuItem(value: 'mkv', child: Text('MKV')),
                            DropdownMenuItem(
                                value: 'webm', child: Text('WEBM')),
                          ],
                    onChanged: (value) {
                      if (value != null)
                        setState(() => _downloadFormat = value);
                    },
                    decoration: const InputDecoration(
                        labelText: 'Formato', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: _downloadQuality,
                    items: _downloadMode == 'audio'
                        ? const [
                            DropdownMenuItem(
                                value: '128k', child: Text('128k')),
                            DropdownMenuItem(
                                value: '192k', child: Text('192k')),
                            DropdownMenuItem(
                                value: '256k', child: Text('256k')),
                            DropdownMenuItem(
                                value: '320k', child: Text('320k')),
                          ]
                        : const [
                            DropdownMenuItem(
                                value: '360p', child: Text('360p')),
                            DropdownMenuItem(
                                value: '480p', child: Text('480p')),
                            DropdownMenuItem(
                                value: '720p', child: Text('720p')),
                            DropdownMenuItem(
                                value: '1080p', child: Text('1080p')),
                            DropdownMenuItem(
                                value: '1440p', child: Text('1440p')),
                            DropdownMenuItem(
                                value: '2160p', child: Text('2160p')),
                          ],
                    onChanged: (value) {
                      if (value != null)
                        setState(() => _downloadQuality = value);
                    },
                    decoration: const InputDecoration(
                        labelText: 'Qualidade', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 14),
                  if (!_isLoading)
                    ElevatedButton(
                      onPressed: () async {
                        setState(() => _isLoading = true);
                        final url = _downloadUrl.text.trim();
                        if (url.isEmpty) {
                          await _setStatus('Informe a URL para download');
                          return;
                        }

                        try {
                          await _setStatus('Obtendo informações...');
                          final info = await _api.getVideoInfo(url);
                          final title = info?['title'] ?? 'Vídeo/Áudio';

                          await NotificationService.show(
                            'Download Iniciado',
                            'Baixando: $title',
                          );

                          await _setStatus('Iniciando download...');
                          final t = await _api.download(
                            url: url,
                            mode: _downloadMode,
                            format: _downloadFormat,
                            quality: _downloadQuality,
                          );

                          setState(() {
                            _taskId.text = t;
                          });
                          await _setStatus(
                              'Processando... acompanhando progresso...');
                          _startPolling(t);
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content:
                                    Text('Download iniciado no servidor!')),
                          );
                        } catch (e) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                                content: Text('Erro: $e'),
                                backgroundColor: Colors.red),
                          );
                          await _setStatus('Erro de conexão: $e');
                        } finally {
                          setState(() => _isLoading = false);
                        }
                      },
                      child: const Text('Iniciar Download'),
                    )
                  else
                    const Center(
                      child: Padding(
                        padding: EdgeInsets.all(8.0),
                        child: CircularProgressIndicator(),
                      ),
                    ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _taskId,
                    decoration: const InputDecoration(
                      labelText: 'Task ID (opcional para status)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () async {
                            final id = _taskId.text.trim();
                            if (id.isEmpty) {
                              await _setStatus('Informe Task ID primeiro');
                              return;
                            }
                            final t = await _api.downloadProgress(id);
                            await _setStatus('Progresso: $t');
                          },
                          child: const Text('Ver Progresso'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () async {
                            final id = _taskId.text.trim();
                            if (id.isEmpty) {
                              await _setStatus('Informe Task ID primeiro');
                              return;
                            }
                            final t = await _api.cancelDownload(id);
                            await _setStatus('Cancelado: $t');
                          },
                          child: const Text('Cancelar'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  ElevatedButton(
                    onPressed: _logout,
                    style:
                        ElevatedButton.styleFrom(backgroundColor: Colors.red),
                    child: const Text('Logout'),
                  ),
                  if (_historyItems.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    const Text('Histórico',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    SizedBox(
                      height: 120,
                      child: ListView.builder(
                        itemCount: _historyItems.length,
                        itemBuilder: (context, index) {
                          final item = _historyItems[index];
                          return ListTile(
                            dense: true,
                            title: Text(item['title'] ?? item['url'] ?? ''),
                            subtitle: Text(item['url'] ?? ''),
                          );
                        },
                      ),
                    ),
                  ],
                ],
                const SizedBox(height: 16),
                Text('Status: $_status', style: const TextStyle(fontSize: 16)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
