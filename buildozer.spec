[app]
title = Filament Envanteri
package.name = filamentenvanteri
package.domain = io.github.burstfire47
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0.0
requirements = python3,kivy==2.3.0,pillow,plyer,certifi,pyjnius,android,openssl
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
