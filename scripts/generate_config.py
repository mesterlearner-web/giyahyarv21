# -*- coding: utf-8 -*-
"""
این اسکریپت فقط داخل بیلد خودکار گیت‌هاب (.github/workflows/build.yml)
اجرا می‌شود. config.py را از روی GitHub Secrets می‌سازد تا کلید واقعی
هیچ‌وقت مجبور نباشد داخل خودِ ریپازیتوری (کد یا تاریخچه‌ی گیت) ذخیره شود.

برای تست محلی (python main.py) به این اسکریپت نیازی نیست — همان‌طور که در
config.py.example توضیح داده شده، یک کپی از آن با نام config.py بسازید.

راه‌اندازی: در گیت‌هاب Settings → Secrets and variables → Actions →
New repository secret، این‌ها را (هرکدام که لازم دارید) اضافه کنید:
  DEEPSEEK_API_KEY، PROXY_URL، APP_SHARED_SECRET
اگر هیچ‌کدام را تنظیم نکنید، بیلد همچنان با موفقیت انجام می‌شود؛ فقط اپ در
صفحه‌ی دستیار هوشمند پیام «نیاز به تنظیم» نشان می‌دهد تا وقتی آن‌ها را
اضافه کنید.
"""
import os

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
PROXY_URL = os.environ.get('PROXY_URL', '')
APP_SHARED_SECRET = os.environ.get('APP_SHARED_SECRET', '')

_LINES = [
    f"DEEPSEEK_API_KEY = {DEEPSEEK_API_KEY!r}",
    "DEEPSEEK_API_URL = \"https://api.deepseek.com/chat/completions\"",
    f"PROXY_URL = {PROXY_URL!r}",
    f"APP_SHARED_SECRET = {APP_SHARED_SECRET!r}",
    "VISION_MODEL = \"deepseek-v4-flash-vision-exp\"",
    "TEXT_MODEL = \"deepseek-v4-flash\"",
    "",
]

with open('config.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(_LINES))

if DEEPSEEK_API_KEY:
    status = 'با کلید مستقیم DeepSeek'
elif PROXY_URL:
    status = 'با پراکسی امن'
else:
    status = 'بدون کلید/پراکسی (اپ پیام «نیاز به تنظیم» نشان خواهد داد)'
print(f'✅ config.py ساخته شد — {status}')
