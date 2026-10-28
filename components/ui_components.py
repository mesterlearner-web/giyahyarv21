from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image, AsyncImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.utils import get_color_from_hex
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.core.window import Window
from kivy.animation import Animation
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import rtl, wrap_rtl_text


_LIGHT_COLORS = {
    'primary': get_color_from_hex('#2E7D32'),
    'primary_light': get_color_from_hex('#4CAF50'),
    'primary_dark': get_color_from_hex('#1B5E20'),
    'secondary': get_color_from_hex('#8BC34A'),
    'accent': get_color_from_hex('#FF6F00'),
    'background': get_color_from_hex('#F1F8E9'),
    'card': get_color_from_hex('#FFFFFF'),
    'text_primary': get_color_from_hex('#1B5E20'),
    'text_secondary': get_color_from_hex('#558B2F'),
    'text_dark': get_color_from_hex('#212121'),
    'divider': get_color_from_hex('#C8E6C9'),
    'warning': get_color_from_hex('#F9A825'),
    'error': get_color_from_hex('#C62828'),
    'white': get_color_from_hex('#FFFFFF'),
    'ad_bg': get_color_from_hex('#FFF9C4'),
    'shadow': get_color_from_hex('#00000020'),
}

_DARK_COLORS = {
    'primary': get_color_from_hex('#43A047'),
    'primary_light': get_color_from_hex('#66BB6A'),
    'primary_dark': get_color_from_hex('#2E7D32'),
    'secondary': get_color_from_hex('#9CCC65'),
    'accent': get_color_from_hex('#FFA726'),
    'background': get_color_from_hex('#0F1712'),
    'card': get_color_from_hex('#1A2A1D'),
    'text_primary': get_color_from_hex('#81C784'),
    'text_secondary': get_color_from_hex('#A5C9A8'),
    'text_dark': get_color_from_hex('#E8F0E9'),
    'divider': get_color_from_hex('#2E4A32'),
    'warning': get_color_from_hex('#FFCA28'),
    'error': get_color_from_hex('#EF5350'),
    # 'white' عمداً در هر دو تم یکسان می‌ماند: در کل پروژه فقط برای متن/
    # آیکون روی زمینه‌ی رنگیِ اشباع (هدر، دکمه‌ی primary) استفاده شده، نه
    # برای پس‌زمینه‌ی سطح — پس نیازی به تیره‌شدن ندارد.
    'white': get_color_from_hex('#FFFFFF'),
    'ad_bg': get_color_from_hex('#3D3820'),
    'shadow': get_color_from_hex('#00000060'),
}

# نگاشتِ رنگ‌های هاردکدشده‌ی پرکاربرد در سرتاسر صفحات (تگ‌ها، حباب‌های
# چت، پس‌زمینه‌ی فیلدها و ...) به معادلِ تیره‌شان. تابع theme_hex پایین
# همین صفحه، این نگاشت را اعمال می‌کند تا لازم نباشد صفحات را از نو
# طراحی کنیم — فقط get_color_from_hex('#xxxxxx') را با theme_hex('#xxxxxx')
# عوض می‌کنیم و هر رنگی خودش می‌داند در تمِ تاریک باید چه شکلی باشد.
_TINT_MAP = {
    '#E8F5E9': '#1E3323', '#F1F8E9': '#152018', '#F0F7F0': '#141F16',
    '#F9FBE7': '#1A2015', '#C8E6C9': '#2E4A32', '#A5D6A7': '#4A6B4D',
    '#FFFFFF': '#1A2A1D', '#F5F5F5': '#21262A',
    '#FFEBEE': '#3D1F1F', '#FCE4EC': '#3D1F2A', '#FFCCBC': '#4A342C',
    '#C62828': '#EF5350', '#B71C1C': '#E53935', '#E65100': '#FFA726',
    '#E3F2FD': '#16283A', '#1565C0': '#64B5F6', '#01579B': '#4FC3F7',
    '#E0F7FA': '#0D2B2E', '#00838F': '#4DD0E1',
    '#F3E5F5': '#2A1F33', '#6A1B9A': '#BA68C8', '#880E4F': '#F06292',
    '#FFF8E1': '#332D1A', '#FFF3E0': '#3D2E1A', '#FFF9C4': '#3D3820',
    '#F9A825': '#FFCA28', '#FF6F00': '#FFA726', '#FF9800': '#FFA726',
    '#BDBDBD': '#78909C', '#9E9E9E': '#90A4AE', '#757575': '#B0BEC5',
    '#E0E0E0': '#3A3A3A', '#37474F': '#78909C',
    '#4CAF50': '#66BB6A', '#2E7D32': '#43A047', '#8BC34A': '#9CCC65',
    '#33691E': '#7CB342',
    '#1B5E20': '#81C784', '#558B2F': '#A5C9A8', '#212121': '#E8F0E9',
    '#EFEBE9': '#2A211D', '#4E342E': '#8D6E63', '#5D4037': '#A1887F',
    '#795548': '#BCAAA4',
}

COLORS = dict(_LIGHT_COLORS)
_theme_state = {'dark': False}


def is_dark_theme():
    return _theme_state['dark']


def apply_theme(dark):
    """COLORS را جاگزین نمی‌کند، محتوایش را عوض می‌کند — چون سرتاسر پروژه
    با «from components.ui_components import COLORS» همین یک دیکشنری را
    گرفته‌اند؛ اگر این‌جا COLORS = {...} تازه می‌ساختیم، آن ایمپورت‌های
    قدیمی هنوز به دیکشنریِ کهنه اشاره می‌کردند. توجه: چون هر صفحه فقط
    یک‌بار (در __init__) ساخته می‌شود، برای این‌که رنگ‌های تازه واقعاً
    روی صفحه دیده شوند، باید صفحات از نو ساخته شوند — این کار را
    PlantCareApp.rebuild_all_screens در main.py انجام می‌دهد."""
    _theme_state['dark'] = bool(dark)
    COLORS.clear()
    COLORS.update(_DARK_COLORS if dark else _LIGHT_COLORS)


def theme_hex(light_hex):
    """معادلِ رنگِ فعلی (روشن/تیره) برای یک رنگِ هاردکدشده. برای رنگ‌های
    وضعیتیِ اشباع (که در هر دو تم خواناست) اگر در _TINT_MAP نباشد، همان
    مقدار اصلی برمی‌گردد — یعنی جایگزین‌کردنِ get_color_from_hex با این
    تابع در بدترین حالت بی‌اثر است، نه خراب‌کننده."""
    if not _theme_state['dark']:
        return get_color_from_hex(light_hex)
    dark_hex = _TINT_MAP.get(light_hex.upper(), light_hex)
    return get_color_from_hex(dark_hex)


PLANT_CATEGORY_COLORS = {
    'آپارتمانی': get_color_from_hex('#4CAF50'),
    'گلدار': get_color_from_hex('#E91E63'),
    'دارویی': get_color_from_hex('#009688'),
    'درخت میوه': get_color_from_hex('#FF9800'),
}

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images')
ICONS_DIR = os.path.join(IMAGES_DIR, 'icons')


def icon_path(name):
    """مسیر یک آیکون داخلی (بجای ایموجی، چون فونت باندل‌شده پوشش ایموجی ندارد
    و کیوی روی اندروید fallback خودکار برای گلیف‌های ناموجود انجام نمی‌دهد)."""
    return os.path.join(ICONS_DIR, f'{name}.png')


class PersianTextInput(TextInput):
    """یک TextInput که همزمان با تایپ‌کردن، متن فارسی را حروف‌چینی (اتصال
    حروف) و راست‌چین می‌کند — نه فقط وقتی جای دیگری (یک کارت، یک لیست)
    دوباره نمایش داده می‌شود.

    Kivy به‌طور بنیادین از شکل‌دهی حروف فارسی/عربی حین تایپ پشتیبانی
    نمی‌کند؛ این یک محدودیت شناخته‌شده و قدیمیِ خودِ فریم‌ورک است، نه
    چیزی خاصِ این پروژه (نمونه: github.com/kivy/kivy/issues/1570 از سال
    ۲۰۱۳، همچنان باز). راه‌حلِ تثبیت‌شده override کردن insert_text /
    do_backspace است — دقیقاً نقطه‌ای که خودِ مستندات کیوی برای همین کار
    پیش‌بینی کرده («هر رشته‌ای که تایپ، پیست یا هر جور دیگری وارد
    TextInput شود از این تابع رد می‌شود»).

    **نکته‌ی مهم برای استفاده در بقیه‌ی کد:**
        self.text       → نسخه‌ی نمایشی (حروف‌چینی‌شده/راست‌چین‌شده)،
                          فقط برای رندر کیوی — خودتان مستقیم نخوانید.
        self.raw_text   → نسخه‌ی خام/واقعیِ تایپ‌شده — همیشه همین را برای
                          ذخیره، اعتبارسنجی یا ارسال به API بخوانید.
        از بیرون هم می‌توانید instance.raw_text = '...' ست کنید (مثلاً
        برای خالی‌کردن فرم)؛ نمایش خودش به‌روز می‌شود.

    **محدودیت شناخته‌شده:** بعد از هر تایپ/Backspace، مکان‌نما به انتهای
    متن می‌رود. برای رایج‌ترین حالت استفاده (تایپِ رو به جلو + اصلاح
    فوریِ غلط تایپی با Backspace) این دقیقاً رفتار درست است. اگر با لمس/
    فلش وسطِ متن بروید، خودِ کیوی مکان‌نما را آن‌جا نشان می‌دهد، اما
    اولین کاراکتر بعدی باز هم به انتها اضافه می‌شود — چون موقعیت در متنِ
    راست‌چین‌شده با موقعیت در متنِ خام یکی نیست و نگاشتِ دقیق آن دو به هم
    مشکلی شناخته‌شده و بدون راه‌حل کاملاً تمیز، حتی در نمونه‌های مرجعِ
    منتشرشده برای همین مسئله، است. برای فیلدهای کوتاهِ این اپ (نام
    تایمر، نام گیاه، پیام چت) این یک مصالحه‌ی معقول است.
    """
    raw_text = StringProperty('')

    def __init__(self, **kwargs):
        self._updating = False
        initial = kwargs.pop('text', '') or ''
        super().__init__(**kwargs)
        if initial:
            self.raw_text = initial

    def on_raw_text(self, instance, value):
        self._refresh_display()

    def _refresh_display(self):
        if self._updating:
            return
        self._updating = True
        try:
            if self.raw_text:
                # bidi باید خط‌به‌خط اعمال شود، وگرنه در متنِ چندخطی جهتِ
                # درست رعایت نمی‌شود
                lines = self.raw_text.split('\n')
                display = '\n'.join(rtl(ln) if ln else '' for ln in lines)
            else:
                display = ''
            self.text = display
            self.cursor = self.get_cursor_from_index(len(display))
        finally:
            self._updating = False

    def insert_text(self, substring, from_undo=False):
        if self._updating or not substring:
            return
        if self.selection_text and self.selection_text == self.text:
            # کل متن انتخاب شده بود (مثلاً «انتخاب همه») — جایگزین کن
            self.raw_text = substring
        else:
            # بدون انتخاب، یا انتخابِ جزئی که map‌کردنش به بافرِ خام
            # قابل‌اطمینان نیست؛ برای این‌که چیزی از دست نرود، همیشه به
            # انتهای بافرِ خام اضافه می‌کنیم
            self.raw_text = self.raw_text + substring

    def do_backspace(self, from_undo=False, mode='bkspc'):
        if self._updating:
            return
        if self.selection_text and self.selection_text == self.text:
            self.raw_text = ''
        elif self.raw_text:
            self.raw_text = self.raw_text[:-1]

    def delete_selection(self, from_undo=False):
        if self._updating:
            return
        if self.selection_text and self.selection_text == self.text:
            self.raw_text = ''
        elif self.raw_text:
            self.raw_text = self.raw_text[:-1]


def make_wrapping_label(text, font_size=None, color=None, bold=False,
                        halign='right', valign='top'):
    """برای متنِ بلند و چندخطیِ فارسی (توضیحات گیاه، پاسخ هوش مصنوعی و...)
    به‌جای Label(text=text) معمولی از این استفاده کنید. چرا: اگر متنِ بلند
    مستقیم به سازنده‌ی Label داده شود، پچِ RTL کل رشته را یک‌جا reshape/
    bidi می‌کند و بعد خودِ کیوی آن را بر اساس عرض می‌شکند — چون شکستن روی
    رشته‌ی از قبل بازچینی‌شده اتفاق می‌افتد، ترتیبِ خط‌ها و گاهی کلمات سرِ
    خط درهم/ناقص به نظر می‌رسند. این تابع صبر می‌کند عرضِ واقعیِ ویجت (بعد
    از قرارگرفتن در layout) مشخص شود، بعد با wrap_rtl_text نقطه‌ی شکستِ هر
    خط را روی متنِ اصلی پیدا می‌کند و فقط سپس هر خط را جدا reshape می‌کند."""
    fs = font_size if font_size is not None else sp(14)
    col = color if color is not None else COLORS['text_dark']
    lbl = Label(text='', font_size=fs, color=col, bold=bold,
               size_hint_y=None, halign=halign, valign=valign)

    def _update(instance, value):
        if not lbl.width:
            return
        lbl.text_size = (lbl.width, None)
        lbl.text = wrap_rtl_text(text, font_size=fs, max_width=lbl.width, bold=bold)
    lbl.bind(width=_update)
    lbl.bind(texture_size=lambda i, v: setattr(lbl, 'height', v[1]))
    return lbl


def get_plant_image(image_filename):
    if not image_filename:
        return None
    path = os.path.join(IMAGES_DIR, image_filename)
    if os.path.exists(path):
        return path
    return None


class RoundedCard(FloatLayout):
    radius = NumericProperty(dp(16))
    bg_color = ListProperty([1, 1, 1, 1])
    elevation = NumericProperty(2)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._update_canvas, size=self._update_canvas,
                  bg_color=self._update_canvas)
        from kivy.clock import Clock
        Clock.schedule_once(self._update_canvas, 0)
    
    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:

            Color(0, 0, 0, 0.1)
            RoundedRectangle(
                pos=(self.x + dp(2), self.y - dp(2)),
                size=self.size,
                radius=[self.radius]
            )

            Color(*self.bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius]
            )


class GreenButton(Button):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = COLORS['primary']
        self.color = COLORS['white']
        self.font_size = sp(16)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(50)
        self.bind(pos=self._update_shape, size=self._update_shape)
    
    def _update_shape(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
    
    def on_press(self):
        anim = Animation(background_color=COLORS['primary_dark'], duration=0.1)
        anim.start(self)
    
    def on_release(self):
        anim = Animation(background_color=COLORS['primary'], duration=0.1)
        anim.start(self)


class ToggleSwitch(FloatLayout):
    """سوییچ روشن/خاموشِ سفارشی، چون Switch پیش‌فرض کیوی ظاهری کاملاً
    متفاوت از بقیه‌ی اپ دارد. active را بخوانید/بنویسید؛ on_toggle(bool)
    با هر تغییر (چه لمسِ کاربر، چه ست‌کردنِ دستیِ active از بیرون) صدا
    زده می‌شود."""

    def __init__(self, active=False, on_toggle=None, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (dp(52), dp(30)))
        super().__init__(**kwargs)
        self.active = active
        self.on_toggle = on_toggle

        with self.canvas.before:
            self._bg_color = Color(*(COLORS['primary'] if active else COLORS['divider']))
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        self._knob = Widget(size_hint=(None, None), size=(dp(24), dp(24)))
        with self._knob.canvas.before:
            Color(*COLORS['white'])
            self._knob_bg = Ellipse(pos=self._knob.pos, size=self._knob.size)
        self._knob.bind(pos=self._sync_knob, size=self._sync_knob)
        self.add_widget(self._knob)
        self._sync_bg()

    def _sync_bg(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._bg.radius = [self.height / 2]
        self._position_knob(animate=False)

    def _sync_knob(self, *a):
        self._knob_bg.pos = self._knob.pos
        self._knob_bg.size = self._knob.size

    def _position_knob(self, animate=True):
        pad = dp(3)
        target_x = (self.x + self.width - self._knob.width - pad
                    if self.active else self.x + pad)
        target_y = self.y + (self.height - self._knob.height) / 2
        if animate:
            Animation(x=target_x, y=target_y, duration=0.15, t='out_quad').start(self._knob)
        else:
            self._knob.pos = (target_x, target_y)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.set_active(not self.active)
            return True
        return super().on_touch_down(touch)

    def set_active(self, value):
        self.active = bool(value)
        self._bg_color.rgba = COLORS['primary'] if self.active else COLORS['divider']
        self._position_knob(animate=True)
        if self.on_toggle:
            self.on_toggle(self.active)


class OutlineButton(Button):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = [0, 0, 0, 0]
        self.color = COLORS['primary']
        self.font_size = sp(14)
        self.size_hint_y = None
        self.height = dp(42)
        self.bind(pos=self._update_shape, size=self._update_shape)
    
    def _update_shape(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 0)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*COLORS['primary'])
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=dp(1.5))


class TopBar(BoxLayout):
    title = StringProperty('')
    show_back = BooleanProperty(True)
    
    def __init__(self, app_ref=None, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = [dp(10), dp(5)]
        self.spacing = dp(10)
        
        with self.canvas.before:
            Color(*COLORS['primary'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        self._build()
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
    
    def _build(self):
        if self.show_back:
            back_btn = Button(
                text='←',
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                background_normal='',
                background_color=[0, 0, 0, 0],
                color=COLORS['white'],
                font_size=sp(22),
                bold=True,
            )
            back_btn.bind(on_press=self._go_back)
            self.add_widget(back_btn)
        
        title_label = Label(
            text=self.title,
            color=COLORS['white'],
            font_size=sp(20),
            bold=True,
            halign='center',
        )
        self.add_widget(title_label)
    
    def _go_back(self, instance):
        if self.app_ref:
            self.app_ref.go_back()


class AdBanner(BoxLayout):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(30)
        self.padding = [dp(5), dp(3)]
        self.spacing = dp(5)
        
        with self.canvas.before:
            Color(*COLORS['ad_bg'])
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        

        ad_text = Label(
            text='تبلیغات - اینجا جای تبلیغ شماست',
            font_size=sp(10),
            color=theme_hex('#795548'),
            halign='center',
        )
        ad_small = Label(
            text='Ads',
            font_size=sp(8),
            color=theme_hex('#BDBDBD'),
            size_hint=(None, 1),
            width=dp(25),
        )
        
        self.add_widget(ad_text)
        self.add_widget(ad_small)
    
    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size


class PlantCard(Button):
    
    def __init__(self, plant_data, app_ref=None, **kwargs):
        super().__init__(**kwargs)
        self.plant_data = plant_data
        self.app_ref = app_ref
        self.background_normal = ''
        self.background_color = [0, 0, 0, 0]
        self.size_hint_y = None
        self.height = dp(100)
        
        with self.canvas.before:
            Color(*COLORS['card'])
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            Color(0, 0, 0, 0.05)
            self._shadow = RoundedRectangle(
                pos=(self.x + dp(2), self.y - dp(2)),
                size=self.size, radius=[dp(12)]
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        
        self._build_content()
        self.bind(on_press=self._on_click)
    
    def _update_canvas(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._shadow.pos = (self.x + dp(2), self.y - dp(2))
        self._shadow.size = self.size
    
    def _build_content(self):
        content = BoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            padding=[dp(12), dp(8)],
            size=self.size,
            pos=self.pos,
        )
        self.bind(pos=lambda i, v: setattr(content, 'pos', v),
                  size=lambda i, v: setattr(content, 'size', v))
        

        img_container = BoxLayout(
            size_hint=(None, 1),
            width=dp(82),
        )
        plant_image = PlantImage(
            plant_name=self.plant_data.get('name', ''),
            category=self.plant_data.get('category', 'آپارتمانی'),
            image_path=get_plant_image(self.plant_data.get('image', '')),
            size_hint=(1, 1),
        )
        img_container.add_widget(plant_image)
        

        info_layout = BoxLayout(orientation='vertical', spacing=dp(4))
        
        name_label = Label(
            text=self.plant_data.get('name', ''),
            font_size=sp(15),
            bold=True,
            color=COLORS['text_dark'],
            halign='right',
            valign='middle',
            size_hint_y=None,
            height=dp(28),
        )
        name_label.bind(size=name_label.setter('text_size'))
        
        sci_name = Label(
            text=self.plant_data.get('scientific_name', ''),
            font_size=sp(11),
            color=COLORS['text_secondary'],
            halign='right',
            valign='middle',
            size_hint_y=None,
            height=dp(20),
            italic=True,
        )
        sci_name.bind(size=sci_name.setter('text_size'))
        

        tags_layout = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=None, height=dp(24))
        

        water_tag = self._make_tag(
            self.plant_data.get('watering', ''),
            COLORS['primary_light']
        )
        

        care = self.plant_data.get('care_level', '')
        care_color = COLORS['secondary'] if 'آسان' in care else COLORS['warning'] if 'متوسط' in care else COLORS['error']
        care_tag = self._make_tag(care, care_color)
        
        tags_layout.add_widget(water_tag)
        tags_layout.add_widget(care_tag)
        tags_layout.add_widget(Widget())
        
        info_layout.add_widget(name_label)
        info_layout.add_widget(sci_name)
        info_layout.add_widget(tags_layout)
        

        cat_color = PLANT_CATEGORY_COLORS.get(self.plant_data.get('category', ''), COLORS['primary'])
        cat_label = Label(
            text=self.plant_data.get('category', ''),
            font_size=sp(10),
            color=cat_color,
            size_hint=(None, None),
            size=(dp(60), dp(20)),
            halign='center',
            bold=True,
        )
        
        right_col = BoxLayout(orientation='vertical', size_hint=(None, 1), width=dp(65))
        right_col.add_widget(cat_label)
        right_col.add_widget(Widget())
        

        arrow = Label(
            text='›',
            font_size=sp(24),
            color=COLORS['primary_light'],
            size_hint=(None, None),
            size=(dp(20), dp(30)),
        )
        right_col.add_widget(arrow)
        
        content.add_widget(img_container)
        content.add_widget(info_layout)
        content.add_widget(right_col)
        
        self.add_widget(content)
    
    def _make_tag(self, text, color):
        tag = Label(
            text=text,
            font_size=sp(10),
            color=color,
            size_hint=(None, None),
            size=(dp(75), dp(22)),
            bold=True,
        )
        return tag
    
    def _on_click(self, instance):
        if self.app_ref:
            self.app_ref.show_plant_detail(self.plant_data['id'])


class PlantImage(Widget):

    ICON_MAP = {
        'آپارتمانی': 'ic_leaf',
        'گلدار': 'ic_flower',
        'دارویی': 'ic_herb',
        'درخت میوه': 'ic_fruit',
    }

    def __init__(self, plant_name='', category='آپارتمانی', image_path=None,
                 corner_radius=None, **kwargs):
        super().__init__(**kwargs)
        self.plant_name = plant_name
        self.category = category
        self._fixed_radius = corner_radius
        self._photo = None
        self._fallback_icon = None

        cat_color = PLANT_CATEGORY_COLORS.get(category, COLORS['primary'])

        with self.canvas:
            Color(*cat_color[:3], 0.18)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                         radius=[self._radius()])

        if image_path:
            inset = dp(3)
            self._inset = inset
            self._photo = AsyncImage(
                source=image_path,
                allow_stretch=True,
                keep_ratio=False,
                pos=self._inset_pos(),
                size=self._inset_size(),
            )
            self.add_widget(self._photo)
        else:
            icon_name = self.ICON_MAP.get(category, 'ic_leaf')
            self._fallback_icon = Image(
                source=icon_path(icon_name),
                allow_stretch=True,
                keep_ratio=True,
                pos=self.pos,
                size=self.size,
            )
            self.add_widget(self._fallback_icon)

        self.bind(pos=self._update, size=self._update)

    def _radius(self):
        if self._fixed_radius is not None:
            return self._fixed_radius
        return dp(10)

    def _inset_pos(self):
        return (self.x + self._inset, self.y + self._inset)

    def _inset_size(self):
        return (max(1, self.width - self._inset * 2),
                max(1, self.height - self._inset * 2))

    def _update(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._bg.radius = [self._radius()]
        if self._photo:
            self._photo.pos = self._inset_pos()
            self._photo.size = self._inset_size()
        elif self._fallback_icon:
            # آیکون کمی کوچک‌تر از کل کادر تا مثل یک نشان (badge) به‌نظر برسد
            pad = min(self.width, self.height) * 0.22
            self._fallback_icon.pos = (self.x + pad, self.y + pad)
            self._fallback_icon.size = (self.width - pad * 2, self.height - pad * 2)


class InfoRow(BoxLayout):
    
    def __init__(self, key, value, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(40)
        self.padding = [dp(10), dp(5)]
        
        key_label = Label(
            text=key,
            font_size=sp(13),
            color=COLORS['text_secondary'],
            size_hint=(0.45, 1),
            halign='right',
            valign='middle',
        )
        key_label.bind(size=key_label.setter('text_size'))
        
        separator = Label(text=':', size_hint=(None, 1), width=dp(10), color=COLORS['divider'])
        
        value_label = Label(
            text=value,
            font_size=sp(13),
            color=COLORS['text_dark'],
            bold=True,
            size_hint=(0.55, 1),
            halign='left',
            valign='middle',
        )
        value_label.bind(size=value_label.setter('text_size'))
        
        self.add_widget(key_label)
        self.add_widget(separator)
        self.add_widget(value_label)


class BottomNavBar(BoxLayout):

    def __init__(self, app_ref=None, active_tab='home', **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.active_tab = active_tab
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(60)
        self.spacing = dp(2)
        self.padding = [0, 0, 0, 0]

        self._build()

    def _build(self):
        tabs = [
            ('home', 'ic_home_white', 'خانه'),
            ('plant_list', 'ic_leaf_white', 'گیاهان'),
            ('tools', 'ic_tools_white', 'ابزارها'),
            ('shop', 'ic_cart_white', 'فروشگاه'),
        ]

        dark_green = get_color_from_hex('#1B5E20')
        active_green = COLORS['primary_light']

        for tab_id, icon_name, label in tabs:
            is_active = tab_id == self.active_tab
            btn = Button(
                text='',
                background_normal='',
                background_down='',
                background_color=active_green if is_active else dark_green,
                size_hint_x=1,
            )

            inner = BoxLayout(orientation='vertical', spacing=dp(2),
                               padding=[0, dp(6)],
                               pos=btn.pos, size=btn.size)
            # نکته مهم: 'inner=inner' به‌صورت آرگومان پیش‌فرض لازم است تا مقدار
            # همان دور از حلقه لمس (capture) شود؛ وگرنه چون همه‌ی لامبداها به
            # متغیر حلقه‌ی 'inner' با ارجاع (نه مقدار) وصل می‌شوند، وقتی کیوی
            # این callbackها را بعداً (پس از پایان کل حلقه) صدا می‌زند، همه‌شان
            # به آخرین مقدار 'inner' (تب فروشگاه) اشاره می‌کنند و آیکون/متن سه
            # تب دیگر هیچ‌وقت به موقعیت واقعی دکمه‌ی خودشان منتقل نمی‌شود.
            btn.bind(pos=lambda i, v, inner=inner: setattr(inner, 'pos', v),
                     size=lambda i, v, inner=inner: setattr(inner, 'size', v))

            icon_img = Image(source=icon_path(icon_name), size_hint=(1, 0.55),
                              allow_stretch=True)
            inner.add_widget(icon_img)

            lbl = Label(text=label, font_size=sp(11), bold=True,
                        color=(1, 1, 1, 1), size_hint=(1, 0.45))
            inner.add_widget(lbl)

            btn.add_widget(inner)
            _tab_id = tab_id
            btn.bind(on_press=lambda b, t=_tab_id: self._navigate(t))
            self.add_widget(btn)

    def _navigate(self, tab_id):
        if self.app_ref:
            self.app_ref.go_to_screen(tab_id)


class SectionTitle(Label):
    
    def __init__(self, text='', **kwargs):
        super().__init__(text=text, **kwargs)
        self.font_size = sp(17)
        self.bold = True
        self.color = COLORS['text_primary']
        self.size_hint_y = None
        self.height = dp(40)
        self.halign = 'right'
        self.valign = 'middle'
        self.bind(size=self.setter('text_size'))

