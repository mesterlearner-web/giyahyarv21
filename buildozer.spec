[app]

# عنوان برنامه
title = گیاهیار - مراقبت از گیاهان
package.name = plantcare
package.domain = com.giaahyar

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,ttf
source.include_patterns = images/*.png,images/*.jpg,images/*.jpeg,images/icons/*.png,fonts/*.ttf,data/*.py,screens/*.py,components/*.py,utils/*.py

version = 1.0.0

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,pillow,requests,certifi,urllib3,chardet,charset-normalizer,idna,arabic-reshaper,python-bidi,plyer

orientation = portrait
fullscreen = 0

android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.ndk_api = 21
android.arch = arm64-v8a

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,CAMERA,VIBRATE

icon.filename = %(source.dir)s/images/app_icon.png
presplash.filename = %(source.dir)s/images/splash.jpg
android.presplash_color = #0B030D

android.accept_sdk_license = True
android.logcat_filters = *:S python:D
#android.add_jars =
#android.add_src =
#android.gradle_dependencies =
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer
bin_dir = ./bin
