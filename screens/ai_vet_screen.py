from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.image import Image, AsyncImage
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.animation import Animation

from PIL import Image as PILImage, ImageOps

import io
import os
import sys
import base64
import threading
import requests

from utils.helpers import rtl, wrap_rtl_text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.ui_components import COLORS, AdBanner, GreenButton, SectionTitle, icon_path, PersianTextInput, theme_hex

# کلید و آدرس‌ها را از config.py می‌خوانیم (نه هاردکد داخل همین فایل — به
# docstring بالای config.py نگاه کنید). اگر config.py هنوز ساخته نشده باشد
# (مثلاً کلون تازه‌ی ریپو، یا بیلد گیت‌هابی که Secretهایش ست نشده)، به‌جای
# کرش، با مقادیر خالی ادامه می‌دهیم و همان پیام «نیاز به تنظیم» را که پایین
# همین فایل هم برای خطاهای دیگر استفاده می‌شود نشان می‌دهیم.
try:
    from config import (DEEPSEEK_API_KEY, DEEPSEEK_API_URL, PROXY_URL,
                         APP_SHARED_SECRET, VISION_MODEL, TEXT_MODEL)
except ImportError:
    DEEPSEEK_API_KEY = ''
    DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'
    PROXY_URL = ''
    APP_SHARED_SECRET = ''
    VISION_MODEL = 'deepseek-v4-flash-vision-exp'
    TEXT_MODEL = 'deepseek-v4-flash'


# فیلتر LANCZOS برای resize؛ در نسخه‌های خیلی جدید Pillow مسیر جدید دارد
try:
    _LANCZOS = PILImage.Resampling.LANCZOS
except AttributeError:
    _LANCZOS = PILImage.LANCZOS


SYSTEM_PROMPT = (
    'شما یک متخصص گیاه‌پزشکی و باغبانی حرفه‌ای هستید که فقط به زبان فارسی '
    'پاسخ می‌دهید. در مورد مشکلات گیاهان آپارتمانی، بیماری‌ها، آفات، شرایط '
    'رشد، آبیاری، کوددهی و هر موضوع مرتبط با گیاهان مشاوره‌ی تخصصی، کوتاه، '
    'واضح و کاربردی می‌دهید. وقتی عکسی برایتان فرستاده می‌شود، ابتدا آنچه '
    'در عکس می‌بینید را با اطمینان توصیف و مشکل احتمالی را تشخیص دهید، '
    'سپس یک راهکار درمانی مشخص و عملی پیشنهاد دهید. پاسخ را با جمله‌بندی '
    'ساده و بخش‌بندی‌شده (مثلاً «تشخیص:» و «راهکار:») بنویسید تا خواندنش '
    'راحت باشد. از کاراکترهای ایموجی استفاده نکنید، چون فونت فارسیِ این اپ '
    'پشتیبانی کاملی از نمایش ایموجی ندارد.'
)

# قبل از ارسال، عکس به این اندازه محدود می‌شود. مدل ویژن DeepSeek هر عکس را
# با سقف ثابتی از توکن پردازش می‌کند، پس فرستادن عکس چند مگابایتی خام فقط
# زمان و حجم آپلود (مهم روی اینترنت موبایل) را زیاد می‌کند، بدون افزایش
# دقت تشخیص.
MAX_IMAGE_EDGE = 1024
JPEG_QUALITY = 85
REQUEST_TIMEOUT = 45  # ثانیه


class _DeepSeekError(Exception):
    """خطایی با پیام فارسیِ آماده برای نمایش مستقیم به کاربر."""
    pass


def _encode_image_data_url(path):
    """عکس را باز می‌کند، بر اساس EXIF گوشی می‌چرخاند (وگرنه خیلی از
    عکس‌های دوربین موبایل کج/وارونه به مدل می‌رسند)، در صورت نیاز کوچک
    می‌کند و به‌صورت data URL بازمی‌گرداند. خروجی همیشه JPEG است — حتی اگر
    ورودی PNG/WebP باشد — تا حجم و نوع MIME قابل‌پیش‌بینی بماند."""
    with PILImage.open(path) as img:
        img = ImageOps.exif_transpose(img)

        if img.mode in ('RGBA', 'LA', 'P'):
            rgba = img.convert('RGBA')
            flat = PILImage.new('RGB', rgba.size, (255, 255, 255))
            flat.paste(rgba, mask=rgba.split()[-1])
            img = flat
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        w, h = img.size
        longest = max(w, h)
        if longest > MAX_IMAGE_EDGE:
            scale = MAX_IMAGE_EDGE / float(longest)
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), _LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=JPEG_QUALITY)
        encoded = base64.b64encode(buf.getvalue()).decode('ascii')

    return 'data:image/jpeg;base64,' + encoded


def _post_to_deepseek(payload):
    """درخواست را به DeepSeek (یا در صورت تنظیم‌بودن PROXY_URL، به پراکسی
    امن) می‌فرستد و متن پاسخ مدل را برمی‌گرداند. روی هر نوع خطا (شبکه،
    Timeout، کد غیر ۲۰۰، پاسخ ناقص)، _DeepSeekError با پیام فارسیِ
    قابل‌نمایش raise می‌کند.
    نکته‌ی حیاتی: این تابع شبکه‌محور است و هرگز نباید از ترد اصلی UI صدا
    زده شود — همیشه از داخل threading.Thread فراخوانی می‌شود؛ در غیر
    این‌صورت هنگام انتظار برای پاسخ سرور، کل رابط کاربری فریز می‌شود."""
    use_proxy = bool(PROXY_URL.strip())
    endpoint = PROXY_URL.strip() if use_proxy else DEEPSEEK_API_URL

    headers = {'Content-Type': 'application/json'}
    if use_proxy:
        if APP_SHARED_SECRET:
            headers['X-App-Secret'] = APP_SHARED_SECRET
    else:
        headers['Authorization'] = f'Bearer {DEEPSEEK_API_KEY}'

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.Timeout:
        raise _DeepSeekError('پاسخی از سرور دریافت نشد (زمان درخواست تمام شد). لطفاً دوباره تلاش کنید.')
    except requests.exceptions.ConnectionError:
        raise _DeepSeekError('اتصال اینترنت برقرار نیست. لطفاً اتصال خود را بررسی کنید.')
    except requests.exceptions.RequestException as e:
        raise _DeepSeekError(f'خطا در ارسال درخواست:\n{str(e)[:100]}')

    if resp.status_code == 401:
        raise _DeepSeekError('کلید API نامعتبر یا منقضی است. مقدار DEEPSEEK_API_KEY را در config.py بررسی کنید.')
    if resp.status_code == 429:
        raise _DeepSeekError('محدودیت تعداد درخواست (Rate Limit). چند لحظه صبر کنید و دوباره امتحان کنید.')
    if resp.status_code >= 500:
        raise _DeepSeekError(f'سرور DeepSeek موقتاً در دسترس نیست (کد {resp.status_code}). کمی بعد دوباره امتحان کنید.')
    if resp.status_code != 200:
        detail = ''
        try:
            err_obj = resp.json().get('error')
            detail = err_obj.get('message', '') if isinstance(err_obj, dict) else str(err_obj or '')
        except Exception:
            detail = resp.text[:150]
        raise _DeepSeekError(f'خطا (کد {resp.status_code})\n{detail[:150]}')

    try:
        data = resp.json()
        return data['choices'][0]['message']['content']
    except (KeyError, IndexError, ValueError, TypeError):
        raise _DeepSeekError('پاسخ دریافتی از سرور در قالب مورد انتظار نبود.')


class AIVetScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.mode = 'chat'

        # --- وضعیت تب «چت با متخصص» ---
        self.conversation = []
        self.selected_image_path = None
        self._chat_layout = None
        self._chat_scroll = None
        self._input_field = None
        self._send_btn = None
        self._status_lbl = None
        self._img_status = None
        self._chat_preview = None
        self._chat_clear_img_btn = None
        self._typing_indicator = None

        # --- وضعیت تب «تحلیل تصویر گیاه» ---
        self._vision_image_path = None
        self._vision_preview = None
        self._vision_preview_placeholder = None
        self._vision_fname_lbl = None
        self._vision_remove_btn = None
        self._vision_note_input = None
        self._vision_analyze_btn = None
        self._vision_result_lbl = None
        self._vision_result_scroll = None
        self._vision_result_raw = ''
        self._refresh_vision_result_fn = None
        self._analyzing_popup = None
        self._analyzing_icon = None

        # --- ویجت‌های مشترک ---
        self._title_lbl = None
        self._tab_chat_btn = None
        self._tab_vision_btn = None
        self._chat_panel = None
        self._vision_panel = None
        self._body = None
        self._root = None

        Clock.schedule_once(self._build_ui, 0)

    def on_enter(self):
        # همان تضمینِ لحظه‌ی-ورود که در tools_screen.py/add_plant_screen.py
        # هم اضافه شد: دقیقاً همین لحظه، self.size قطعاً درست/نهایی است.
        if getattr(self, '_fix_layout', None):
            self._fix_layout()
        # اگر از کارت «دستیار هوشمند» یا «مشاوره گیاه‌پزشکی» در صفحه‌ی
        # ابزار مراقبت وارد شده باشیم، ToolsScreen از قبل تعیین کرده کدام
        # تب باز شود (پایین همین کلاس، self.app.pending_ai_vet_mode).
        if self.app and getattr(self.app, 'pending_ai_vet_mode', None):
            desired = self.app.pending_ai_vet_mode
            self.app.pending_ai_vet_mode = None
            if desired in ('chat', 'vision'):
                self._set_mode(desired)

    # ======================================================================
    # ساخت رابط کاربری اصلی + تب‌ها
    # ======================================================================
    def _build_ui(self, dt):
        root = FloatLayout()
        with root.canvas.before:
            Color(*COLORS['background'])
            bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(bg, 'pos', v),
                  size=lambda i, v: setattr(bg, 'size', v))

        header = self._build_header()

        # body = [تب‌ها (ثابت)] + [یکی از دو پنل، بسته به حالت فعال]؛ چون
        # BoxLayout خودش پهنا و ارتفاعِ باقیمانده را بین فرزندانش تقسیم
        # می‌کند، نیازی به محاسبه‌ی دستی موقعیت هر ردیف داخلی نیست.
        body = BoxLayout(orientation='vertical', size_hint=(1, None))
        body.add_widget(self._build_mode_tabs())
        self._body = body

        self._chat_panel = self._build_chat_panel()
        self._vision_panel = self._build_vision_panel()

        ad = AdBanner(size_hint=(None, None), size=(dp(300), dp(30)),
                      pos_hint={'center_x': 0.5})

        root.add_widget(body)
        root.add_widget(header)
        root.add_widget(ad)
        self.add_widget(root)
        self._root = root

        def _fix(*a):
            header_h = dp(60)
            ad_h = dp(30)
            body.pos = (0, ad_h)
            body.height = max(dp(200), self.height - header_h - ad_h)
            ad.pos = (self.width / 2 - dp(150), 0)
        self._fix_layout = _fix
        Clock.schedule_once(_fix, 0.05)
        # همان مشکلی که در tools_screen.py/add_plant_screen.py روی گوشی
        # واقعی دیده شد: چون body با size_hint_y=None ساخته شده (ارتفاعش
        # را دستی می‌دهیم)، اگر تنها اجرا self.height را قبل از این‌که این
        # صفحه واقعاً روی صفحه‌نمایش بیاید محاسبه کند، برای همیشه با
        # ارتفاع اشتباه/خالی می‌ماند. این‌جا هم همان تضمینِ دوگانه را
        # می‌گذاریم: هم روی هر تغییر اندازه، هم روی هر بار ورود واقعی.
        self.bind(size=_fix)

        self._add_bot_message(
            'سلام! من دستیار گیاه‌پزشکی گیاهیار هستم.\n\n'
            'می‌توانید:\n'
            '• سوال‌های مراقبتی بپرسید یا مشکل گیاهتان را توضیح دهید\n'
            '• از تب «تحلیل تصویر گیاه» یک عکس بفرستید تا مستقیماً بررسی شود\n\n'
            'چطور می‌توانم کمک کنم؟'
        )
        self._set_mode('chat')

    def _build_header(self):
        header = BoxLayout(orientation='horizontal', size_hint=(1, None),
                           height=dp(60), padding=[dp(10), dp(8)], spacing=dp(6),
                           pos_hint={'top': 1})
        with header.canvas.before:
            Color(*COLORS['primary'])
            hbg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(hbg, 'pos', v),
                    size=lambda i, v: setattr(hbg, 'size', v))

        back_btn = Button(text='←', font_size=sp(22), size_hint=(None, 1), width=dp(44),
                          background_normal='', background_color=[0, 0, 0, 0],
                          color=COLORS['white'])
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('tools', 'right'))

        self._title_lbl = Label(text='دستیار هوشمند گیاهیار', font_size=sp(17),
                                bold=True, color=COLORS['white'],
                                halign='right', valign='middle')
        self._title_lbl.bind(size=self._title_lbl.setter('text_size'))

        header.add_widget(back_btn)
        header.add_widget(self._title_lbl)
        return header

    def _build_mode_tabs(self):
        bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(44),
                        padding=[dp(10), dp(6)], spacing=dp(8))
        with bar.canvas.before:
            Color(*COLORS['card'])
            bbg = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda i, v: setattr(bbg, 'pos', v),
                 size=lambda i, v: setattr(bbg, 'size', v))

        self._tab_chat_btn = self._make_tab_btn('چت با متخصص', 'chat')
        self._tab_vision_btn = self._make_tab_btn('تحلیل تصویر گیاه', 'vision')
        bar.add_widget(self._tab_chat_btn)
        bar.add_widget(self._tab_vision_btn)
        return bar

    def _make_tab_btn(self, text, mode):
        is_active = (mode == self.mode)
        btn = Button(text=text, font_size=sp(13), bold=is_active,
                    background_normal='', background_color=[0, 0, 0, 0],
                    color=COLORS['white'] if is_active else COLORS['text_secondary'])
        with btn.canvas.before:
            color_instr = Color(*(COLORS['primary'] if is_active else COLORS['background']))
            rect_instr = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(10)])
        btn.bind(pos=lambda i, v, r=rect_instr: setattr(r, 'pos', v),
                 size=lambda i, v, r=rect_instr: setattr(r, 'size', v))
        btn._bg_color_instr = color_instr
        btn.bind(on_press=lambda x, m=mode: self._set_mode(m))
        return btn

    def _style_tabs(self):
        for btn, m in ((self._tab_chat_btn, 'chat'), (self._tab_vision_btn, 'vision')):
            is_active = (m == self.mode)
            btn._bg_color_instr.rgba = COLORS['primary'] if is_active else COLORS['background']
            btn.color = COLORS['white'] if is_active else COLORS['text_secondary']
            btn.bold = is_active

    def _set_mode(self, mode):
        if not self._chat_panel or not self._vision_panel or not self._body:
            return
        self.mode = mode
        if self._chat_panel.parent:
            self._body.remove_widget(self._chat_panel)
        if self._vision_panel.parent:
            self._body.remove_widget(self._vision_panel)

        if mode == 'vision':
            self._body.add_widget(self._vision_panel)
            self._title_lbl.text = rtl('تحلیل تصویر با هوش مصنوعی')
        else:
            self._body.add_widget(self._chat_panel)
            self._title_lbl.text = rtl('مشاوره با متخصص گیاه‌پزشکی')

        self._style_tabs()

    # ======================================================================
    # تب «چت با متخصص»
    # ======================================================================
    def _build_chat_panel(self):
        panel = BoxLayout(orientation='vertical')

        self._status_lbl = Label(
            text=self._chat_status_text(), font_size=sp(11),
            color=COLORS['text_secondary'], halign='center', valign='middle',
        )
        self._status_lbl.bind(size=self._status_lbl.setter('text_size'))
        status_bar = BoxLayout(size_hint_y=None, height=dp(26), padding=[dp(8), dp(2)])
        with status_bar.canvas.before:
            Color(*theme_hex('#F9FBE7'))
            sbbg = Rectangle(pos=status_bar.pos, size=status_bar.size)
        status_bar.bind(pos=lambda i, v: setattr(sbbg, 'pos', v),
                        size=lambda i, v: setattr(sbbg, 'size', v))
        status_bar.add_widget(self._status_lbl)

        chat_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self._chat_layout = BoxLayout(orientation='vertical', size_hint_y=None,
                                      spacing=dp(10), padding=[dp(10), dp(8)])
        self._chat_layout.bind(minimum_height=self._chat_layout.setter('height'))
        # ScrollView خودش size_hint_x فرزندش را به پیکسل واقعی تبدیل نمی‌کند
        chat_scroll.bind(width=self._chat_layout.setter('width'))
        chat_scroll.add_widget(self._chat_layout)
        self._chat_scroll = chat_scroll

        input_area = self._build_chat_input_area()

        panel.add_widget(status_bar)
        panel.add_widget(chat_scroll)
        panel.add_widget(input_area)
        return panel

    def _build_chat_input_area(self):
        input_area = BoxLayout(orientation='vertical', size_hint=(1, None),
                               height=dp(140), padding=[dp(8), dp(6)], spacing=dp(6))
        with input_area.canvas.before:
            Color(*COLORS['card'])
            iabg = Rectangle(pos=input_area.pos, size=input_area.size)
        input_area.bind(pos=lambda i, v: setattr(iabg, 'pos', v),
                        size=lambda i, v: setattr(iabg, 'size', v))

        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(48), spacing=dp(6))
        img_btn = Button(
            text='ارسال عکس', font_size=sp(12), size_hint=(None, 1), width=dp(100),
            background_normal='', background_color=theme_hex('#E3F2FD'),
            color=theme_hex('#1565C0'),
        )
        img_btn.bind(on_press=lambda x: self._open_image_picker(self._on_chat_image_picked))

        self._chat_preview = AsyncImage(source='', size_hint=(None, 1), width=dp(38),
                                        opacity=0, allow_stretch=True, keep_ratio=True)

        self._img_status = Label(text='', font_size=sp(11), color=COLORS['text_secondary'],
                                 halign='right', valign='middle')
        self._img_status.bind(size=self._img_status.setter('text_size'))

        self._chat_clear_img_btn = Button(
            text='X', font_size=sp(13), bold=True, size_hint=(None, 1), width=dp(30),
            background_normal='', background_color=[0, 0, 0, 0],
            color=theme_hex('#C62828'), opacity=0, disabled=True,
        )
        self._chat_clear_img_btn.bind(on_press=self._clear_chat_image)

        clear_btn = Button(
            text='پاک کردن چت', font_size=sp(11), size_hint=(None, 1), width=dp(88),
            background_normal='', background_color=theme_hex('#FFEBEE'),
            color=theme_hex('#C62828'),
        )
        clear_btn.bind(on_press=self._clear_chat)

        btn_row.add_widget(img_btn)
        btn_row.add_widget(self._chat_preview)
        btn_row.add_widget(self._img_status)
        btn_row.add_widget(self._chat_clear_img_btn)
        btn_row.add_widget(Widget())
        btn_row.add_widget(clear_btn)

        text_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60), spacing=dp(8))
        self._input_field = PersianTextInput(
            hint_text='سوال یا مشکل گیاه خود را بنویسید...',
            font_size=sp(14), multiline=True, halign='right',
            background_color=theme_hex('#F1F8E9'),
            foreground_color=COLORS['text_dark'],
            hint_text_color=theme_hex('#A5D6A7'),
        )
        self._send_btn = Button(
            text='ارسال', font_size=sp(13), bold=True, size_hint=(None, 1), width=dp(56),
            background_normal='', background_color=COLORS['primary'], color=COLORS['white'],
        )
        self._send_btn.bind(on_press=self._send_message)
        text_row.add_widget(self._input_field)
        text_row.add_widget(self._send_btn)

        input_area.add_widget(btn_row)
        input_area.add_widget(text_row)
        return input_area

    def _chat_status_text(self):
        # این مقدار مستقیم به سازنده‌ی Label داده می‌شود (پایین همین فایل)،
        # پس نباید این‌جا rtl() بخورد؛ پچ سراسری در main.py خودش موقع
        # ساخت هر Label این کار را انجام می‌دهد. rtl() کردنش این‌جا هم،
        # باعث دوبار ریشیپ/بازچینی و متن به‌هم‌ریخته می‌شد.
        if DEEPSEEK_API_KEY or PROXY_URL:
            return 'آنلاین — دستیار آماده‌ی مشاوره است'
        return 'نیاز به تنظیم کلید API — به config.py یا server/README.md مراجعه کنید'

    def _make_bot_avatar(self, diameter=36, icon_size=20):
        """یک آواتار دایره‌ای برای پیام‌های ربات می‌سازد (آیکون PNG داخل
        دایره‌ی رنگی، نه ایموجی — چون فونت فارسیِ باندل‌شده پوشش ایموجی
        ندارد و کیوی fallback خودکار انجام نمی‌دهد). چون یک ویجت نمی‌تواند
        هم‌زمان در دو والد باشد، هر بار که آواتار لازم شود این تابع صدا زده
        می‌شود تا نمونه‌ی تازه بسازد."""
        d = dp(diameter)
        avatar = FloatLayout(size_hint=(None, None), size=(d, d))
        with avatar.canvas.before:
            Color(*COLORS['primary'])
            circle = Ellipse(pos=avatar.pos, size=avatar.size)
        avatar.bind(pos=lambda i, v: setattr(circle, 'pos', v),
                    size=lambda i, v: setattr(circle, 'size', v))
        icon = Image(source=icon_path('ic_bot_white'), size_hint=(None, None),
                    size=(dp(icon_size), dp(icon_size)),
                    pos_hint={'center_x': 0.5, 'center_y': 0.5})
        avatar.add_widget(icon)
        return avatar

    def _add_bot_message(self, text):
        msg_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                            spacing=dp(8), padding=[dp(0), dp(4)])
        avatar = self._make_bot_avatar()

        bubble = BoxLayout(size_hint_y=None, padding=dp(12))
        with bubble.canvas.before:
            Color(*theme_hex('#E8F5E9'))
            bbg = RoundedRectangle(pos=bubble.pos, size=bubble.size, radius=[dp(12)])
        bubble.bind(pos=lambda i, v: setattr(bbg, 'pos', v),
                    size=lambda i, v: setattr(bbg, 'size', v))

        bubble_width = self.width * 0.68
        msg_lbl = Label(
            text='', font_size=sp(13), color=COLORS['text_dark'],
            halign='right', valign='top', text_size=(bubble_width, None),
        )
        # متن را این‌جا (بعد از ساختنِ Label با text='') ست می‌کنیم، نه در
        # سازنده — چون اگر مستقیم در سازنده می‌دادیم، پچِ RTL کل پیام را
        # یک‌جا reshape می‌کرد و بعد کیوی آن را روی رشته‌ی از قبل
        # بازچینی‌شده می‌شکست (باعثِ ناقص/درهم دیده‌شدنِ کلمات سرِ خط
        # می‌شود، مخصوصاً در پاسخ‌های بلندِ هوش مصنوعی). wrap_rtl_text خودش
        # هر خط را جدا و درست reshape می‌کند.
        msg_lbl.text = wrap_rtl_text(text, font_size=sp(13), max_width=bubble_width)
        msg_lbl.bind(texture_size=lambda i, v: setattr(msg_lbl, 'height', v[1] + dp(4)))
        bubble.add_widget(msg_lbl)
        bubble.bind(minimum_height=bubble.setter('height'))

        def _update_h(*a):
            bubble.height = msg_lbl.height + dp(24)
            msg_box.height = max(dp(52), bubble.height + dp(8))
        msg_lbl.bind(height=_update_h)
        Clock.schedule_once(lambda dt: _update_h(), 0.05)

        msg_box.add_widget(avatar)
        msg_box.add_widget(bubble)
        msg_box.add_widget(Widget())

        if self._chat_layout:
            self._chat_layout.add_widget(msg_box)
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

    def _add_user_message(self, text, has_image=False):
        prefix = '[با عکس پیوست‌شده] ' if has_image else ''
        msg_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                            spacing=dp(8), padding=[dp(0), dp(4)])

        bubble = BoxLayout(size_hint_y=None, padding=dp(12))
        with bubble.canvas.before:
            Color(*COLORS['primary'])
            bbg = RoundedRectangle(pos=bubble.pos, size=bubble.size, radius=[dp(12)])
        bubble.bind(pos=lambda i, v: setattr(bbg, 'pos', v),
                    size=lambda i, v: setattr(bbg, 'size', v))

        bubble_width = self.width * 0.68
        msg_lbl = Label(
            text='', font_size=sp(13), color=COLORS['white'],
            halign='right', valign='top', text_size=(bubble_width, None),
        )
        msg_lbl.text = wrap_rtl_text(f'{prefix}{text}', font_size=sp(13), max_width=bubble_width)
        msg_lbl.bind(texture_size=lambda i, v: setattr(msg_lbl, 'height', v[1] + dp(4)))
        bubble.add_widget(msg_lbl)

        def _update_h(*a):
            bubble.height = msg_lbl.height + dp(24)
            msg_box.height = max(dp(44), bubble.height + dp(8))
        msg_lbl.bind(height=_update_h)
        Clock.schedule_once(lambda dt: _update_h(), 0.05)

        # پیام‌های کاربر آواتار ندارند (فقط حباب رنگی راست‌چین) — هم UI
        # ساده‌تر می‌ماند، هم نیازی به آیکون «کاربر» که در پروژه موجود
        # نیست نمی‌افتد.
        msg_box.add_widget(Widget())
        msg_box.add_widget(bubble)

        if self._chat_layout:
            self._chat_layout.add_widget(msg_box)
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

    def _add_typing_indicator(self):
        typing = BoxLayout(orientation='horizontal', size_hint_y=None,
                           height=dp(44), spacing=dp(8), padding=[dp(4), dp(4)])
        typing.add_widget(self._make_bot_avatar(diameter=36, icon_size=20))
        dots_box = BoxLayout(size_hint_y=None, height=dp(36), padding=dp(8))
        with dots_box.canvas.before:
            Color(*theme_hex('#E8F5E9'))
            dbbg = RoundedRectangle(pos=dots_box.pos, size=dots_box.size, radius=[dp(10)])
        dots_box.bind(pos=lambda i, v: setattr(dbbg, 'pos', v),
                      size=lambda i, v: setattr(dbbg, 'size', v))
        dots_box.add_widget(Label(text='در حال تایپ...', font_size=sp(12), color=COLORS['text_secondary']))
        typing.add_widget(dots_box)
        typing.add_widget(Widget())
        if self._chat_layout:
            self._chat_layout.add_widget(typing)
            self._typing_indicator = typing
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)

    def _remove_typing_indicator(self):
        if self._typing_indicator and self._chat_layout and self._typing_indicator in self._chat_layout.children:
            self._chat_layout.remove_widget(self._typing_indicator)
        self._typing_indicator = None

    def _send_message(self, instance):
        text = self._input_field.raw_text.strip() if self._input_field else ''
        if not text:
            return

        has_image = self.selected_image_path is not None
        self._add_user_message(text, has_image=has_image)
        self._input_field.raw_text = ''
        if self._send_btn:
            self._send_btn.disabled = True
        self._add_typing_indicator()

        image_path = self.selected_image_path
        self._clear_chat_image()

        threading.Thread(target=self._prepare_and_call_api, args=(text, image_path), daemon=True).start()

    def _prepare_and_call_api(self, text, image_path):
        """در ترد پس‌زمینه: عکس (اگر پیوست شده) را Base64/بهینه می‌کند، به
        مکالمه اضافه می‌کند و سپس تماس شبکه را انجام می‌دهد. عمداً همه‌ی
        این مراحل (نه فقط خودِ درخواست شبکه) داخل ترد است تا Base64-کردن
        یک عکس دوربین گوشی هم UI را حتی برای یک لحظه هنگ نکند."""
        try:
            if image_path:
                data_url = _encode_image_data_url(image_path)
                content = [
                    {'type': 'text', 'text': text},
                    {'type': 'image_url', 'image_url': {'url': data_url}},
                ]
            else:
                content = text
            self.conversation.append({'role': 'user', 'content': content})
        except Exception as e:
            msg = f'خطا در پردازش عکس:\n{str(e)[:100]}'
            Clock.schedule_once(lambda dt, m=msg: self._on_api_response(m), 0)
            return

        self._call_api()

    def _call_api(self):
        if not (DEEPSEEK_API_KEY or PROXY_URL):
            Clock.schedule_once(lambda dt: self._on_api_response(self._setup_needed_message()), 0)
            return
        try:
            model = VISION_MODEL if self._conversation_has_image() else TEXT_MODEL
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}] + self.conversation
            payload = {'model': model, 'messages': messages, 'max_tokens': 1024}
            reply = _post_to_deepseek(payload)
            self.conversation.append({'role': 'assistant', 'content': reply})
            Clock.schedule_once(lambda dt, r=reply: self._on_api_response(r), 0)
        except _DeepSeekError as e:
            Clock.schedule_once(lambda dt, m=str(e): self._on_api_response(m), 0)
        except Exception as e:
            msg = f'خطای غیرمنتظره:\n{str(e)[:100]}'
            Clock.schedule_once(lambda dt, m=msg: self._on_api_response(m), 0)

    def _conversation_has_image(self):
        # فقط مدل ویژن عکس قبول می‌کند؛ اگر هر پیامی در تاریخچه‌ی مکالمه
        # عکس داشته باشد (حتی چند پیام قبل)، باید همچنان از مدل ویژن
        # استفاده کرد وگرنه درخواست با خطا برمی‌گردد.
        for msg in self.conversation:
            content = msg.get('content')
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'image_url':
                        return True
        return False

    def _setup_needed_message(self):
        return (
            'راه‌اندازی دستیار هوشمند هنوز کامل نشده.\n\n'
            'یک کلید DeepSeek در config.py قرار دهید (یا برای انتشار عمومیِ '
            'اپ، PROXY_URL را برای استفاده از پراکسی امن تنظیم کنید).\n'
            'راهنمای کامل: server/README.md'
        )

    def _on_api_response(self, reply):
        self._remove_typing_indicator()
        self._add_bot_message(reply)
        if self._send_btn:
            self._send_btn.disabled = False

    def _on_chat_image_picked(self, path):
        if not path:
            return
        self.selected_image_path = path
        fname = os.path.basename(path)
        if self._img_status:
            self._img_status.text = rtl(fname[:22])
        if self._chat_preview:
            self._chat_preview.source = path
            self._chat_preview.opacity = 1
            self._chat_preview.reload()
        if self._chat_clear_img_btn:
            self._chat_clear_img_btn.opacity = 1
            self._chat_clear_img_btn.disabled = False

    def _clear_chat_image(self, *args):
        self.selected_image_path = None
        if self._img_status:
            self._img_status.text = ''
        if self._chat_preview:
            self._chat_preview.source = ''
            self._chat_preview.opacity = 0
        if self._chat_clear_img_btn:
            self._chat_clear_img_btn.opacity = 0
            self._chat_clear_img_btn.disabled = True

    def _clear_chat(self, *args):
        self.conversation = []
        self._clear_chat_image()
        if self._chat_layout:
            self._chat_layout.clear_widgets()
        self._add_bot_message('چت پاک شد. چطور می‌توانم کمک کنم؟')

    def _scroll_to_bottom(self, *args):
        if self._chat_scroll:
            self._chat_scroll.scroll_y = 0

    # ======================================================================
    # تب «تحلیل تصویر گیاه» — دکمه‌ی انتخاب عکس → پیش‌نمایش → تحلیل → نتیجه
    # ======================================================================
    def _build_vision_panel(self):
        panel = BoxLayout(orientation='vertical')

        top_controls = BoxLayout(orientation='vertical', size_hint=(1, None),
                                 height=dp(330), padding=[dp(14), dp(12)], spacing=dp(10))

        self._vision_pick_btn = GreenButton(text='انتخاب عکس گیاه')
        self._vision_pick_btn.bind(on_press=lambda x: self._open_image_picker(self._on_vision_image_picked))

        preview_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(110), spacing=dp(12))
        preview_frame = FloatLayout(size_hint=(None, 1), width=dp(110))
        with preview_frame.canvas.before:
            Color(*theme_hex('#E8F5E9'))
            pf_bg = RoundedRectangle(pos=preview_frame.pos, size=preview_frame.size, radius=[dp(10)])
        preview_frame.bind(pos=lambda i, v: setattr(pf_bg, 'pos', v),
                           size=lambda i, v: setattr(pf_bg, 'size', v))

        self._vision_preview_placeholder = BoxLayout(
            orientation='vertical', size_hint=(1, 1), padding=dp(10), spacing=dp(4),
        )
        self._vision_preview_placeholder.add_widget(Image(
            source=icon_path('ic_leaf'), size_hint=(1, None), height=dp(30),
        ))
        ph_lbl = Label(text='عکسی انتخاب نشده', font_size=sp(10.5),
                       color=COLORS['text_secondary'], halign='center')
        self._vision_preview_placeholder.add_widget(ph_lbl)
        self._vision_preview = AsyncImage(source='', size_hint=(1, 1), opacity=0,
                                          allow_stretch=True, keep_ratio=True)
        preview_frame.add_widget(self._vision_preview_placeholder)
        preview_frame.add_widget(self._vision_preview)

        preview_info = BoxLayout(orientation='vertical', spacing=dp(6))
        self._vision_fname_lbl = Label(
            text='هنوز عکسی انتخاب نکرده‌اید', font_size=sp(12),
            color=COLORS['text_secondary'], halign='right', valign='top',
        )
        self._vision_fname_lbl.bind(size=self._vision_fname_lbl.setter('text_size'))
        self._vision_remove_btn = Button(
            text='حذف عکس', font_size=sp(11), size_hint=(None, None), size=(dp(92), dp(30)),
            background_normal='', background_color=theme_hex('#FFEBEE'),
            color=theme_hex('#C62828'), opacity=0, disabled=True,
        )
        self._vision_remove_btn.bind(on_press=self._clear_vision_image)
        preview_info.add_widget(self._vision_fname_lbl)
        preview_info.add_widget(self._vision_remove_btn)
        preview_info.add_widget(Widget())

        preview_row.add_widget(preview_frame)
        preview_row.add_widget(preview_info)

        self._vision_note_input = PersianTextInput(
            hint_text='توضیح مشکل (اختیاری) — مثلاً: برگ‌ها زرد شده‌اند...',
            font_size=sp(13), multiline=True, size_hint_y=None, height=dp(64),
            halign='right',
            background_color=theme_hex('#F1F8E9'),
            foreground_color=COLORS['text_dark'],
            hint_text_color=theme_hex('#A5D6A7'),
        )

        self._vision_analyze_btn = GreenButton(text='تحلیل با هوش مصنوعی')
        self._vision_analyze_btn.disabled = True
        self._vision_analyze_btn.bind(on_press=self._start_analysis)

        top_controls.add_widget(self._vision_pick_btn)
        top_controls.add_widget(preview_row)
        top_controls.add_widget(self._vision_note_input)
        top_controls.add_widget(self._vision_analyze_btn)

        result_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        result_inner = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(14), dp(12)])
        result_inner.bind(minimum_height=result_inner.setter('height'))
        result_scroll.bind(width=result_inner.setter('width'))

        self._vision_result_raw = self._vision_placeholder_text()
        self._vision_result_lbl = Label(
            text='', font_size=sp(13.5),
            color=COLORS['text_secondary'], size_hint_y=None, halign='right', valign='top',
        )

        def _refresh_vision_result(*a):
            w = self._vision_result_lbl.width
            if not w:
                return
            self._vision_result_lbl.text_size = (w, None)
            self._vision_result_lbl.text = wrap_rtl_text(
                self._vision_result_raw, font_size=sp(13.5), max_width=w)
        self._refresh_vision_result_fn = _refresh_vision_result
        self._vision_result_lbl.bind(width=_refresh_vision_result)
        self._vision_result_lbl.bind(texture_size=lambda i, v: setattr(self._vision_result_lbl, 'height', v[1]))
        result_inner.add_widget(self._vision_result_lbl)
        result_scroll.add_widget(result_inner)
        self._vision_result_scroll = result_scroll

        panel.add_widget(top_controls)
        panel.add_widget(SectionTitle(text='نتیجه‌ی تحلیل'))
        panel.add_widget(result_scroll)
        return panel

    def _vision_placeholder_text(self):
        # همان دلیل _chat_status_text: تنها مصرف‌کننده‌ی این تابع یک
        # سازنده‌ی Label است که خودش rtl() را اعمال می‌کند؛ اینجا دوباره
        # rtl() کردن، متن را دوبار ریشیپ/بازچینی و به‌هم‌ریخته می‌کرد.
        return (
            'پس از انتخاب عکس گیاه و لمس «تحلیل با هوش مصنوعی»،\n'
            'نتیجه‌ی تشخیص و راهکار درمانی اینجا نمایش داده می‌شود.'
        )

    def _on_vision_image_picked(self, path):
        if not path:
            return
        self._vision_image_path = path
        fname = os.path.basename(path)
        if self._vision_fname_lbl:
            self._vision_fname_lbl.text = rtl(fname[:40])
        if self._vision_preview:
            self._vision_preview.source = path
            self._vision_preview.opacity = 1
            self._vision_preview.reload()
        if self._vision_preview_placeholder:
            self._vision_preview_placeholder.opacity = 0
        if self._vision_remove_btn:
            self._vision_remove_btn.opacity = 1
            self._vision_remove_btn.disabled = False
        if self._vision_analyze_btn:
            self._vision_analyze_btn.disabled = False

    def _clear_vision_image(self, *args):
        self._vision_image_path = None
        if self._vision_fname_lbl:
            self._vision_fname_lbl.text = rtl('هنوز عکسی انتخاب نکرده‌اید')
        if self._vision_preview:
            self._vision_preview.source = ''
            self._vision_preview.opacity = 0
        if self._vision_preview_placeholder:
            self._vision_preview_placeholder.opacity = 1
        if self._vision_remove_btn:
            self._vision_remove_btn.opacity = 0
            self._vision_remove_btn.disabled = True
        if self._vision_analyze_btn:
            self._vision_analyze_btn.disabled = True

    def _start_analysis(self, instance):
        if not self._vision_image_path:
            self._show_message('لازم است', 'ابتدا یک عکس از گیاه انتخاب کنید.')
            return
        if self._vision_analyze_btn:
            self._vision_analyze_btn.disabled = True
        self._show_analyzing_popup()
        note = self._vision_note_input.raw_text if self._vision_note_input else ''
        threading.Thread(target=self._run_vision_analysis,
                         args=(self._vision_image_path, note), daemon=True).start()

    def _run_vision_analysis(self, image_path, note_text):
        """این تابع کامل در یک ترد پس‌زمینه اجرا می‌شود: خواندن/بهینه‌سازی/
        Base64-کردن عکس + درخواست شبکه — هیچ‌کدام روی ترد اصلی UI نیست."""
        if not (DEEPSEEK_API_KEY or PROXY_URL):
            msg = self._setup_needed_message()
            Clock.schedule_once(lambda dt, m=msg: self._on_vision_result(m, True), 0)
            return
        try:
            data_url = _encode_image_data_url(image_path)
            note_text = (note_text or '').strip()
            prompt_text = note_text if note_text else (
                'این گیاه چه مشکلی دارد؟ لطفاً بیماری، آفت یا مشکل احتمالی را '
                'با توجه به عکس تشخیص بده و یک راهکار درمانی مشخص و عملی '
                'پیشنهاد بده.'
            )
            payload = {
                'model': VISION_MODEL,
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt_text},
                            {'type': 'image_url', 'image_url': {'url': data_url}},
                        ],
                    },
                ],
                'max_tokens': 800,
            }
            reply = _post_to_deepseek(payload)
            Clock.schedule_once(lambda dt, r=reply: self._on_vision_result(r, False), 0)
        except _DeepSeekError as e:
            Clock.schedule_once(lambda dt, m=str(e): self._on_vision_result(m, True), 0)
        except Exception as e:
            msg = f'خطای غیرمنتظره در پردازش عکس:\n{str(e)[:100]}'
            Clock.schedule_once(lambda dt, m=msg: self._on_vision_result(m, True), 0)

    def _on_vision_result(self, text, is_error):
        self._dismiss_analyzing_popup()
        if self._vision_analyze_btn:
            self._vision_analyze_btn.disabled = False
        if self._vision_result_lbl:
            self._vision_result_lbl.color = COLORS['error'] if is_error else COLORS['text_dark']
            self._vision_result_raw = text
            if self._refresh_vision_result_fn:
                self._refresh_vision_result_fn()
        if self._vision_result_scroll:
            Clock.schedule_once(lambda dt: setattr(self._vision_result_scroll, 'scroll_y', 1), 0.05)

    def _show_analyzing_popup(self):
        content = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(14))
        with content.canvas.before:
            Color(*COLORS['card'])
            _ac_bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda i, v: setattr(_ac_bg, 'pos', v),
                    size=lambda i, v: setattr(_ac_bg, 'size', v))

        # BoxLayout عمودی pos_hint فرزندانش را رعایت نمی‌کند (خودش موقعیت
        # را بر اساس چیدمانش محاسبه می‌کند)، پس برای وسط‌چین کردن یک ویجت
        # با عرض ثابت، از همان ترفند ردیفِ اسپیسر استفاده می‌کنیم که در
        # add_plant_screen.py (icon_box) هم به کار رفته.
        icon_row = BoxLayout(size_hint_y=None, height=dp(56))
        icon_row.add_widget(Widget())
        icon_box = FloatLayout(size_hint=(None, None), size=(dp(56), dp(56)))
        with icon_box.canvas.before:
            Color(*COLORS['primary'])
            circle = Ellipse(pos=icon_box.pos, size=icon_box.size)
        icon_box.bind(pos=lambda i, v: setattr(circle, 'pos', v),
                      size=lambda i, v: setattr(circle, 'size', v))
        icon_box.add_widget(Image(source=icon_path('ic_medical_white'), size_hint=(None, None),
                                  size=(dp(30), dp(30)), pos_hint={'center_x': 0.5, 'center_y': 0.5}))
        icon_row.add_widget(icon_box)
        icon_row.add_widget(Widget())
        content.add_widget(icon_row)
        content.add_widget(Label(text='در حال تحلیل تصویر...', font_size=sp(16), bold=True,
                                 color=COLORS['primary'], size_hint_y=None, height=dp(28)))
        content.add_widget(Label(text='لطفاً چند لحظه صبر کنید', font_size=sp(12),
                                 color=COLORS['text_secondary'], size_hint_y=None, height=dp(22)))
        popup = Popup(title='', separator_height=0, content=content,
                     size_hint=(0.75, 0.34), auto_dismiss=False)

        pulse = Animation(opacity=0.35, duration=0.55) + Animation(opacity=1, duration=0.55)
        pulse.repeat = True
        pulse.start(icon_box)

        self._analyzing_popup = popup
        self._analyzing_icon = icon_box
        popup.open()

    def _dismiss_analyzing_popup(self):
        if self._analyzing_icon:
            Animation.cancel_all(self._analyzing_icon)
            self._analyzing_icon = None
        if self._analyzing_popup:
            self._analyzing_popup.dismiss()
            self._analyzing_popup = None

    # ======================================================================
    # کمکی‌های مشترک
    # ======================================================================
    def _open_image_picker(self, on_picked):
        """گالری گوشی را باز می‌کند. ابتدا plyer را امتحان می‌کند (روی
        اندروید، انتخابگر بومی گالری/Photos را باز می‌کند که با محدودیت‌های
        دسترسی ذخیره‌سازی اندروید ۱۱+ سازگار است)؛ اگر در دسترس نبود (مثلاً
        هنگام تست دسکتاپ بدون plyer نصب‌شده)، به FileChooser داخلی کیوی
        برمی‌گردد. on_picked(path) با مسیر فایل انتخاب‌شده (یا None در صورت
        انصراف) صدا زده می‌شود؛ چون منبع این callback ممکن است ترد اصلی UI
        نباشد، همیشه از طریق Clock.schedule_once فراخوانی می‌شود."""
        try:
            from plyer import filechooser

            def _handle_selection(selection):
                path = selection[0] if selection else None
                Clock.schedule_once(lambda dt: on_picked(path), 0)

            filechooser.open_file(
                title='انتخاب عکس گیاه',
                multiple=False,
                filters=[['Images', '*.png', '*.jpg', '*.jpeg', '*.webp']],
                on_selection=_handle_selection,
            )
        except Exception as e:
            print(f'plyer.filechooser در دسترس نیست ({e})؛ استفاده از FileChooser داخلی کیوی')
            self._open_image_picker_fallback(on_picked)

    def _open_image_picker_fallback(self, on_picked):
        from kivy.uix.filechooser import FileChooserIconView
        fc = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg', '*.webp'])
        popup = Popup(title=rtl('انتخاب عکس گیاه'), content=fc, size_hint=(0.95, 0.85))

        def _select(chooser, selection, touch):
            if selection:
                popup.dismiss()
                Clock.schedule_once(lambda dt: on_picked(selection[0]), 0)

        fc.bind(on_submit=_select)
        popup.open()

    def _show_message(self, title, msg):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        with content.canvas.before:
            Color(*COLORS['card'])
            _mc_bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda i, v: setattr(_mc_bg, 'pos', v),
                    size=lambda i, v: setattr(_mc_bg, 'size', v))
        content.add_widget(Label(text=msg, font_size=sp(14), color=COLORS['text_dark'], halign='center'))
        ok_btn = Button(text='باشه', size_hint_y=None, height=dp(44),
                       background_normal='', background_color=COLORS['primary'], color=COLORS['white'])
        content.add_widget(ok_btn)
        popup = Popup(title=rtl(title), content=content, size_hint=(0.8, 0.3), auto_dismiss=True)
        ok_btn.bind(on_press=lambda x: popup.dismiss())
        popup.open()
