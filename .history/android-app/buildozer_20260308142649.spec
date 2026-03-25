[app]

# Título do app
title = YouTube Downloader Pro

# Nome do pacote
package.name = youtubedownloaderpro

# Domínio do pacote (para android/ios)
package.domain = org.youtubedownloader

# Código fonte
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Versão
version = 1.0.0

# Requisitos (pyjnius==1.6.1 e cython<3 para compatibilidade)
requirements = python3,kivy,pyjnius==1.6.1,cython<3,yt-dlp,pycryptodomex==3.17,blake2b-py

# Permissões Android
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,POST_NOTIFICATIONS

# Orientação
orientation = portrait

# Modo fullscreen
fullscreen = 0

# Android API
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Arquitetura
android.archs = arm64-v8a,armeabi-v7a

# Aceitar licenças automaticamente
android.accept_sdk_license = True

# Ícone do app
icon.filename = %(source.dir)s/icon.png

# Presplash (tela de carregamento)
presplash.filename = %(source.dir)s/presplash.png

# Cor de fundo do presplash
android.presplash_color = #1a1a2e

# Gradle
android.gradle_dependencies = 

# Android features
android.features = android.intent.action.SEND

# Whitelist
android.whitelist = 

# Blacklist
android.blacklist = 

# Adiciona python path
android.add_src = 

# Logcat
log_level = 2

# Debug mode
android.debug = False

# P4A branch
p4a.branch = master

# Backup
android.allow_backup = True

[buildozer]

# Nível de log (0 = error, 1 = info, 2 = debug)
log_level = 2

# Avisos como erros
warn_on_root = 1

# Diretório de build
build_dir = ./.buildozer

# Diretório de bin
bin_dir = ./bin
