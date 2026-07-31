[app]
title = Offline AI Study App
package.name = studyapp
package.domain = org.offlineai
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gguf,onnx,json
source.include_patterns = piper/*, llama.cpp/build/bin/*

version = 1.0.0
requirements = python3,kivy

orientation = portrait
fullscreen = 0

# Android Permissions
permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Android Specifics
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
