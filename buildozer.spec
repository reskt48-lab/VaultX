[app]

title = VaultX
package.name = vaultx
package.domain = org.vaultx

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,webp,json,env
source.exclude_exts = pyc,pyo

version = 1.0.0

requirements = python3,kivy,plyer,supabase,python-dotenv,cryptography

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.archs = arm64-v8a,armeabi-v7a

android.permissions = INTERNET,READ_MEDIA_IMAGES

android.private_storage = True
android.allow_backup = False

[buildozer]

log_level = 2
warn_on_root = 1