import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;

Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('FCM background message ${message.messageId}');
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  late final FirebaseMessaging _messaging;
  late final WebViewController _controller;
  final String backendUrl = 'http://<IP-DO-PC>:8000';
  final String fletUrl = 'http://<IP-DO-PC>:8555';

  @override
  void initState() {
    super.initState();
    _messaging = FirebaseMessaging.instance;
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(Uri.parse(fletUrl));

    _initFcm();
    FirebaseMessaging.onMessage.listen(_onMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_onMessageOpenedApp);
  }

  void _onMessage(RemoteMessage message) {
    if (message.notification != null) {
      final title = message.notification?.title ?? 'Notificação';
      final body = message.notification?.body ?? '';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$title: $body')),
      );
    }
  }

  void _onMessageOpenedApp(RemoteMessage message) {
    debugPrint('Notificação aberta: ${message.messageId}');
  }

  Future<void> _initFcm() async {
    NotificationSettings settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      final token = await _messaging.getToken();
      debugPrint('FCM token: $token');
      if (token != null) {
        try {
          await http.post(
            Uri.parse('$backendUrl/fcm/register_token'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode({'user_id': 'mobile_user_1', 'fcm_token': token}),
          );
          debugPrint('Token registrado com sucesso.');
        } catch (e) {
          debugPrint('Erro ao registrar token: $e');
        }
      }
    } else {
      debugPrint('Permissão de push negada: $settings');
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'YouTube Downloader Wrapper',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: Scaffold(
        appBar: AppBar(title: const Text('YouTube Downloader (WebView)')),
        body: WebView(
          initialUrl: fletUrl,
          javascriptMode: JavascriptMode.unrestricted,
          onWebViewCreated: (WebViewController webViewController) {},
        ),
      ),
    );
  }
}
