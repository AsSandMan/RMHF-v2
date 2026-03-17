# setup.py
from setuptools import setup
import os

APP = ['app.py']
DATA_FILES = []  # сюда можно добавить иконку позже

OPTIONS = {
    'argv_emulation': True,
    'packages': ['flask', 'webview', 'jinja2', 'werkzeug', 'itsdangerous', 'click'],
    'includes': ['WebKit', 'Foundation'],
    'excludes': [
        'PyInstaller',                 # полностью исключить PyInstaller
        'gi', 'gi.repository',         # GObject introspection — не нужен
        'gi.repository.Graphene',      # конкретный виновник
        '_gtkagg', '_tkagg', 'curses', # лишние GUI-бэкенды
        'tkinter', 'Tkinter',          # если не используешь tkinter
    ],
    'plist': {
        'CFBundleName': 'Моя Бухгалтерия',
        'CFBundleDisplayName': 'Моя Бухгалтерия',
        'CFBundleGetInfoString': "Домашняя бухгалтерия",
        'CFBundleIdentifier': "com.yourname.homefinance",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHighResolutionCapable': True,
    },
    # 'iconfile': 'icon.icns',       # раскомментируй позже, когда будет иконка
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)