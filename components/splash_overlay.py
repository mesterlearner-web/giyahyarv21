# -*- coding: utf-8 -*-
"""
اسپلشِ داخل اپ (ادامه‌ی پری‌اسپلشِ بومیِ اندروید).

چرا لازم است؟
پری‌اسپلشِ اندروید (images/splash.jpg در buildozer.spec) را خودِ سیستم‌عامل
نشان می‌دهد و به‌محض این‌که کیوی پنجره‌اش را بسازد برداشته می‌شود. از آن
لحظه تا وقتی اولین فریمِ واقعیِ اپ روی صفحه بیاید، چیزی برای نمایش وجود
ندارد و صفحه سیاه می‌ماند — چون ساختنِ ۱۰ صفحه (به‌خصوص لیست‌های ۸۵ گیاه)
ترد اصلی را چند ثانیه مشغول نگه می‌دارد. این ویجت، دقیقاً همان عکس را با
همان رنگ زمینه، به‌عنوان اولین فریمِ کیوی نشان می‌دهد تا کاربر هیچ
سیاهی‌ای نبیند، و در همین مدت یک نشانگر لودینگ نشان می‌دهد.

نکته‌ی مهم: رنگ SPLASH_BG_HEX باید با android.presplash_color در
buildozer.spec یکی باشد، تا حاشیه‌های احتمالیِ دو طرف (در گوشی‌هایی که نسبت
تصویرشان با عکس فرق دارد) کاملاً یکدست دیده شوند.
"""
import time

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from utils.helpers import rtl, to_persian_num

# رنگ‌ها از خودِ عکس اسپلش اندازه‌گیری شده‌اند (زمینه‌ی تیره و لیموییِ عنوان).
SPLASH_BG_HEX = '#0B030D'
SPLASH_ACCENT_HEX = '#C4FC00'


class _ArcSpinner(Widget):
    """حلقه‌ی کم‌رنگ + یک کمانِ لیمویی که دور آن می‌چرخد. زاویه را بیرون
    (SplashOverlay._tick) تغییر می‌دهد."""
    angle = NumericProperty(0)

    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        self._lw = dp(3)
        with self.canvas:
            Color(1, 1, 1, 0.12)
            self._track = Line(circle=(0, 0, 1), width=self._lw)
            Color(*color)
            self._arc = Line(circle=(0, 0, 1, 0, 100), width=self._lw, cap='round')
        self.bind(pos=self._redraw, size=self._redraw, angle=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        cx, cy = self.center
        r = max(1, min(self.width, self.height) / 2 - self._lw)
        self._track.circle = (cx, cy, r)
        a = self.angle
        self._arc.circle = (cx, cy, r, a, a + 100)


class _ProgressBar(Widget):
    """نوار باریکِ پیشرفت (۰ تا ۱)."""
    progress = NumericProperty(0)

    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(1, 1, 1, 0.12)
            self._track = RoundedRectangle(radius=[dp(3)])
            Color(*color)
            self._fill = RoundedRectangle(radius=[dp(3)])
        self.bind(pos=self._redraw, size=self._redraw, progress=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        self._track.pos = self.pos
        self._track.size = self.size
        # حداقلِ عرض = ارتفاع، تا گوشه‌های گرد در ابتدای کار خراب نشوند
        w = max(self.height, self.width * self.progress) if self.progress > 0 else 0
        self._fill.pos = self.pos
        self._fill.size = (w, self.height)


class SplashOverlay(FloatLayout):
    """
    روی همه‌ی صفحه‌ها قرار می‌گیرد و تا آماده‌شدنِ اپ می‌ماند.

    استفاده:
        splash = SplashOverlay(image_path, min_seconds=2.0)
        splash.set_progress(0.4)        # پیشرفتِ واقعی (۰ تا ۱) — هر وقت خواستید
        splash.finish(on_done=callback) # وقتی همه‌چیز ساخته شد

    min_seconds حداقلِ زمانِ نمایش است: اگر اپ سریع‌تر آماده شود، اسپلش
    تا این مدت می‌ماند (و نوار پیشرفت هم به‌اندازه‌ی همین زمان پر می‌شود)؛
    اگر کندتر آماده شود، اسپلش تا آماده‌شدنِ واقعی می‌ماند.
    """

    def __init__(self, image_path, min_seconds=2.0, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self._min_seconds = max(0.0, float(min_seconds))
        self._t0 = time.monotonic()
        self._real = 0.0        # پیشرفتِ واقعیِ بارگذاری
        self._shown = 0.0       # آنچه روی نوار نشان داده می‌شود (نرم‌شده)
        self._ready = False
        self._fading = False
        self._on_done = None
        self._last_pct = -1

        bg = get_color_from_hex(SPLASH_BG_HEX)
        accent = get_color_from_hex(SPLASH_ACCENT_HEX)

        with self.canvas.before:
            Color(*bg)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda i, v: setattr(self._bg, 'pos', v),
                  size=lambda i, v: setattr(self._bg, 'size', v))

        # همان رفتارِ پری‌اسپلشِ بومی: کلِ عکس، وسط‌چین، بدون برش
        self._img = Image(source=image_path, fit_mode='contain',
                          size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.add_widget(self._img)

        # نشانگر لودینگ در فضای خالیِ بین عنوان و «Made by»
        # (در عکس: حدود ۴۷٪ تا ۷۹٪ ارتفاع از بالا؛ مرکز ≈ ۳۷٪ از پایین)
        box = BoxLayout(orientation='vertical', spacing=dp(10),
                        size_hint=(0.6, None), height=dp(104),
                        pos_hint={'center_x': 0.5, 'center_y': 0.37})

        spinner_row = FloatLayout(size_hint_y=None, height=dp(48))
        self._spinner = _ArcSpinner(accent, size_hint=(None, None),
                                    size=(dp(44), dp(44)),
                                    pos_hint={'center_x': 0.5, 'center_y': 0.5})
        spinner_row.add_widget(self._spinner)

        self._label = Label(text='در حال بارگذاری...', font_size=sp(13),
                            color=(accent[0], accent[1], accent[2], 0.9),
                            size_hint_y=None, height=dp(22),
                            halign='center', valign='middle')

        self._bar = _ProgressBar(accent, size_hint_y=None, height=dp(5))

        box.add_widget(spinner_row)
        box.add_widget(self._label)
        box.add_widget(self._bar)
        self.add_widget(box)

        self._tick_ev = Clock.schedule_interval(self._tick, 1 / 30.)

    # ------------------------------------------------------------------
    # API بیرونی
    # ------------------------------------------------------------------
    def set_progress(self, value):
        """پیشرفتِ واقعیِ بارگذاری (۰ تا ۱). فقط رو به جلو می‌رود."""
        self._real = max(self._real, min(1.0, float(value)))

    def finish(self, on_done=None):
        """همه‌چیز آماده است؛ بعد از رسیدن به حداقل زمان، اسپلش محو می‌شود."""
        self._real = 1.0
        self._ready = True
        self._on_done = on_done

    # ------------------------------------------------------------------
    # داخلی
    # ------------------------------------------------------------------
    def _tick(self, dt):
        elapsed = time.monotonic() - self._t0

        if self._min_seconds > 0:
            target = min(self._real, elapsed / self._min_seconds)
        else:
            target = self._real

        # حرکتِ نرمِ نوار (فقط رو به جلو). بعد از یک مکثِ طولانی (ساختنِ یک
        # صفحه‌ی سنگین) dt بزرگ است و نوار یک‌جا به هدف می‌رسد.
        if target > self._shown:
            self._shown += (target - self._shown) * min(1.0, dt * 10)
            if target - self._shown < 0.002:
                self._shown = target
        self._bar.progress = self._shown

        self._spinner.angle = (self._spinner.angle + dt * 300) % 360

        pct = int(self._shown * 100)
        if pct != self._last_pct:
            self._last_pct = pct
            # بعد از ساخته‌شدنِ Label، پچِ سراسریِ RTL دیگر اعمال نمی‌شود؛
            # پس این‌جا خودمان rtl() می‌کنیم.
            self._label.text = rtl(f'در حال بارگذاری... {to_persian_num(pct)}٪')

        if (self._ready and not self._fading
                and elapsed >= self._min_seconds and self._shown >= 0.995):
            self._begin_fade()

    def _begin_fade(self):
        self._fading = True
        self._shown = 1.0
        self._bar.progress = 1.0
        self._label.text = rtl(f'در حال بارگذاری... {to_persian_num(100)}٪')
        anim = Animation(opacity=0, duration=0.4, t='out_quad')
        anim.bind(on_complete=self._on_faded)
        anim.start(self)

    def _on_faded(self, *args):
        if self._tick_ev:
            self._tick_ev.cancel()
            self._tick_ev = None
        # آزادکردنِ تکسچرِ عکس (حدود ۱۲ مگابایت حافظه‌ی گرافیکی)
        self._img.source = ''
        if self.parent:
            self.parent.remove_widget(self)
        if self._on_done:
            self._on_done()

    # تا وقتی اسپلش روی صفحه است، هیچ لمسی نباید به صفحه‌های زیرش برسد
    def on_touch_down(self, touch):
        return True

    def on_touch_move(self, touch):
        return True

    def on_touch_up(self, touch):
        return True
