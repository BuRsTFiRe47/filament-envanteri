[app]
title = Filament Envanteri
package.name = filamentenvanteri
package.domain = io.github.burstfire47
source.dir = .
source.include_exts = py,png,jpg,kv,txt
version = 1.3.6
requirements = hostpython3==3.11.5,python3==3.11.5,kivy==2.3.0,sqlite3,pillow,certifi,pyjnius,android,openssl
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.ndk = 25b
android.enable_androidx = True
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0
android.add_compile_options = "sourceCompatibility = 1.8", "targetCompatibility = 1.8"
p4a.branch = v2024.01.21
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
