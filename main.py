import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import (StringProperty, NumericProperty, BooleanProperty, 
                              ListProperty, ObjectProperty, DictProperty)
from kivy.storage.jsonstore import JsonStore
from kivy.utils import get_color_from_hex, platform
from kivy.lang import Builder

import json
import time
import threading
from datetime import datetime, timedelta

from utils.helpers import rtl
from components.ui_components import icon_path, apply_theme, is_dark_theme, COLORS, IMAGES_DIR
from components.splash_overlay import SplashOverlay, SPLASH_BG_HEX


from kivy.core.text import LabelBase

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
LabelBase.register(
    name='Roboto',
    fn_regular=os.path.join(_FONT_DIR, 'Persian-Regular.ttf'),
    fn_bold=os.path.join(_FONT_DIR, 'Persian-Bold.ttf'),
    fn_italic=os.path.join(_FONT_DIR, 'Persian-Regular.ttf'),
    fn_bolditalic=os.path.join(_FONT_DIR, 'Persian-Bold.ttf'),
)


from kivy.uix.label import Label as _BaseLabel
from kivy.uix.textinput import TextInput as _BaseTextInput

_original_label_init = _BaseLabel.__init__


def _rtl_label_init(self, **kwargs):
    if 'text' in kwargs:
        kwargs['text'] = rtl(kwargs['text'])
    _original_label_init(self, **kwargs)


_BaseLabel.__init__ = _rtl_label_init

_original_textinput_init = _BaseTextInput.__init__


def _rtl_textinput_init(self, **kwargs):
    if 'hint_text' in kwargs:
        kwargs['hint_text'] = rtl(kwargs['hint_text'])
    _original_textinput_init(self, **kwargs)


_BaseTextInput.__init__ = _rtl_textinput_init


# تنظیم اندازه پنجره فقط برای شبیه‌سازی موبایل روی دسکتاپ (تست با
# python main.py). روی خودِ اندروید نباید اعمال بشه - اگه بشه، فضای
# منطقی ویجت‌ها به همین اندازه‌ی کوچک محدود می‌مونه و برنامه فقط تو
# گوشه‌ی صفحه (پایین-چپ، بر اساس مبدأ مختصات کیوی) رندر می‌شه، هرچند
# رنگ پس‌زمینه کل صفحه رو پر می‌کنه - دقیقاً همون چیزی که رخ داده بود.
if platform != 'android':
    Window.size = (390, 844)

# رنگ پس‌زمینه‌ی عادیِ اپ؛ بعد از محو شدنِ اسپلش اعمال می‌شود
# (_on_boot_finished). تا آن موقع پس‌زمینه‌ی پنجره همرنگِ اسپلش (تیره) است
# تا حتی یک فلاشِ روشن بین پری‌اسپلشِ بومی و اسپلشِ داخل اپ دیده نشود.
APP_BG_COLOR = get_color_from_hex('#F0F7F0')
Window.clearcolor = get_color_from_hex(SPLASH_BG_HEX)

# حداقل زمانِ نمایش اسپلش (ثانیه). اگر اپ زودتر آماده شود، اسپلش و نوارِ
# لودینگ تا این مدت می‌مانند؛ اگر دیرتر آماده شود، تا آماده‌شدنِ واقعی.
# اگر می‌خواهید اسپلش دقیقاً ۸ ثانیه (یا بیشتر) بماند، همین عدد را ۸ بگذارید.
SPLASH_MIN_SECONDS = 2.0

# نکته: ایمپورتِ data.plants_db و همه‌ی صفحه‌ها (screens.*) عمداً از بالای
# این فایل برداشته شد و به مرحله‌ی بارگذاریِ پشتِ اسپلش (_boot_steps پایین)
# رفت؛ وگرنه همه‌ی آن‌ها (از جمله PIL و requests در ai_vet_screen) قبل از
# اولین فریم اجرا می‌شدند و همان صفحه‌ی سیاه را طولانی‌تر می‌کردند.


class PlantCareApp(App):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'گیاهیار - مراقبت از گیاهان'
        self.icon = 'images/app_icon.png'
        

        self.store = JsonStore('plant_care_data.json')
        self.custom_plants_store = JsonStore('custom_plants.json')

        # تمِ ذخیره‌شده را قبل از ساختن هر صفحه‌ای اعمال می‌کنیم؛ چون هر
        # صفحه فقط یک‌بار در build() ساخته می‌شود و رنگ‌هایش را همان لحظه
        # از COLORS می‌خواند، اگر تم را بعداً عوض کنیم صفحات از قبل‌ساخته
        # شده رنگشان عوض نمی‌شود (برای همین toggle_theme پایین همین فایل،
        # به‌جای فقط عوض‌کردن تم، همه‌ی صفحات را از نو می‌سازد).
        try:
            self.dark_mode = bool(
                self.store.get('settings')['dark_mode']
            ) if self.store.exists('settings') else False
        except Exception:
            self.dark_mode = False
        apply_theme(self.dark_mode)
        

        # لیست گیاهان (داخلی + سفارشی) در مرحله‌ی دوم بارگذاری پشتِ اسپلش
        # پر می‌شود (_boot_steps)، چون PLANTS_DATA دیگر بالای فایل ایمپورت
        # نمی‌شود. هیچ صفحه‌ای قبل از پُر شدنش ساخته نمی‌شود.
        self.all_plants = []
        self._get_plant_by_id = None
        self._screen_specs = []   # [(name, class), ...] بعد از ایمپورتِ صفحه‌ها

        # وضعیتِ بارگذاری پشتِ اسپلش
        self._splash = None
        self._boot_gen = None
        self._boot_wait = 0

        self.current_plant = None
        self.screen_manager = None

        # قبل از رفتن به صفحه‌ی دستیار هوشمند (که دو تب چت/تحلیل‌تصویر
        # دارد)، ToolsScreen این را ست می‌کند تا مشخص شود کدام تب باز شود؛
        # AIVetScreen.on_enter آن را می‌خواند و بلافاصله None می‌کند.
        self.pending_ai_vet_mode = None
    
    def _create_screens(self):
        """لیستِ نمونه‌های تازه‌ی همه‌ی صفحات. هم build() اولیه از این
        استفاده می‌کند، هم rebuild_all_screens (بعد از عوض‌شدن تم)."""
        return [cls(name=name) for name, cls in self._screen_specs]

    def build(self):
        # فقط ScreenManager (خالی) + اسپلش ساخته می‌شود تا build() فوراً
        # برگردد و اولین فریمی که روی صفحه می‌آید خودِ اسپلش باشد (نه سیاهی).
        # ساختنِ صفحه‌ها بعداً و مرحله‌به‌مرحله انجام می‌شود (_boot_steps).
        self.screen_manager = ScreenManager(transition=SlideTransition())

        root = FloatLayout()
        root.add_widget(self.screen_manager)

        self._splash = SplashOverlay(
            os.path.join(IMAGES_DIR, 'splash.jpg'),
            min_seconds=SPLASH_MIN_SECONDS,
        )
        root.add_widget(self._splash)

        # چند فریمِ اول صبر می‌کنیم تا اسپلش واقعاً روی صفحه رسم شود؛ بعد
        # بارگذاری شروع می‌شود. (Clock.schedule_once(…, 0) کافی نیست، چون
        # کال‌بک‌های همان تیکِ اول قبل از اولین رسم اجرا می‌شوند.)
        self._boot_gen = self._boot_steps()
        self._boot_wait = 3
        Clock.schedule_interval(self._boot_tick, 0)

        return root

    def _boot_tick(self, dt):
        """هر تیکِ Clock صدا زده می‌شود؛ هر بار یک مرحله از _boot_steps را
        اجرا می‌کند و بعد چند فریم صبر می‌کند تا اسپلش (نوار و چرخنده) رسم
        شود و صفحه‌ی ساخته‌شده‌ی آن مرحله کارش (_build_ui) تمام شود."""
        if self._boot_wait > 0:
            self._boot_wait -= 1
            return
        try:
            self._boot_wait = next(self._boot_gen)
        except StopIteration:
            return False   # unschedule

    def _boot_steps(self):
        """مراحل بارگذاری. هر `yield n` یعنی «n فریم صبر کن و بعد برو مرحله‌ی
        بعد». چون ویجت‌های کیوی فقط روی ترد اصلی ساخته می‌شوند، نمی‌شود این
        کارها را در ترد جدا انجام داد؛ ولی با تکه‌تکه کردن، هر تکه بین دو
        فریم اجرا می‌شود و اسپلش بین آن‌ها زنده می‌ماند (فقط وسطِ ساختنِ یک
        صفحه‌ی سنگین، مثل لیست گیاهان، چرخنده لحظه‌ای می‌ایستد)."""
        splash = self._splash

        # ۱) داده‌ی گیاهان
        splash.set_progress(0.03)
        yield 2
        from data.plants_db import PLANTS_DATA, get_plant_by_id
        self._get_plant_by_id = get_plant_by_id
        self.all_plants = list(PLANTS_DATA)
        self.load_custom_plants()
        splash.set_progress(0.10)
        yield 2

        # ۲) ایمپورتِ کلاس‌های صفحه‌ها (شاملِ PIL و requests)
        from screens.home_screen import HomeScreen
        from screens.plant_list_screen import PlantListScreen
        from screens.plant_detail_screen import PlantDetailScreen
        from screens.tools_screen import ToolsScreen
        from screens.timer_screen import TimerScreen
        from screens.ai_vet_screen import AIVetScreen
        from screens.shop_screen import ShopScreen
        from screens.add_plant_screen import AddPlantScreen
        from screens.search_screen import SearchScreen
        from screens.settings_screen import SettingsScreen
        self._screen_specs = [
            ('home', HomeScreen),
            ('plant_list', PlantListScreen),
            ('plant_detail', PlantDetailScreen),
            ('tools', ToolsScreen),
            ('timers', TimerScreen),
            ('ai_vet', AIVetScreen),
            ('shop', ShopScreen),
            ('add_plant', AddPlantScreen),
            ('search', SearchScreen),
            ('settings', SettingsScreen),
        ]
        splash.set_progress(0.25)
        yield 2

        # ۳) ساختنِ صفحه‌ها، یکی‌یکی. سازنده‌ی هر صفحه، ساختنِ رابطش
        # (_build_ui) را با Clock.schedule_once برای فریمِ بعد می‌گذارد؛ پس
        # بعد از هر صفحه چند فریم صبر می‌کنیم تا آن کار تمام و رسم شود.
        # screen.app باید همین‌جا (قبل از _build_ui) ست شود، دقیقاً مثل قبل.
        total = len(self._screen_specs)
        for i, (name, cls) in enumerate(self._screen_specs):
            splash.set_progress(0.25 + 0.70 * i / total)
            screen = cls(name=name)
            screen.app = self
            self.screen_manager.add_widget(screen)
            yield 2

        self.screen_manager.current = 'home'
        splash.finish(on_done=self._on_boot_finished)

    def _on_boot_finished(self):
        Window.clearcolor = APP_BG_COLOR
        self._splash = None

    def toggle_theme(self):
        """تم را عوض، در JsonStore ذخیره و همه‌ی صفحات را از نو می‌سازد تا
        رنگ‌های تازه واقعاً روی صفحه دیده شوند (توضیح کامل بالای __init__)."""
        self.dark_mode = not self.dark_mode
        try:
            self.store.put('settings', dark_mode=self.dark_mode)
        except Exception as e:
            print(f"خطا در ذخیره‌ی تنظیمات: {e}")
        apply_theme(self.dark_mode)
        self.rebuild_all_screens(return_to='settings')

    def rebuild_all_screens(self, return_to='home'):
        if not self.screen_manager:
            return
        self.screen_manager.clear_widgets()
        for screen in self._create_screens():
            screen.app = self
            self.screen_manager.add_widget(screen)
        self.screen_manager.current = return_to
    
    def load_custom_plants(self):
        try:
            if self.custom_plants_store.exists('plants'):
                custom = self.custom_plants_store.get('plants')['data']
                self.all_plants.extend(custom)
        except Exception as e:
            print(f"خطا در لود گیاهان: {e}")
    
    def add_custom_plant(self, plant_data):
        plant_data['id'] = len(self.all_plants) + 1000
        # قبلاً اینجا 'default_plant.jpg' ست می‌شد، فایلی که اصلاً در
        # images/ وجود ندارد. چون get_plant_image() برای فایل ناموجود None
        # برمی‌گرداند، این باعث نمی‌شد کرش کند، ولی PlantImage/PlantCard را
        # مجبور می‌کرد هر بار یک os.path.exists() بی‌فایده روی مسیر غلط
        # انجام دهند. با خالی گذاشتن 'image'، همان مسیر fallback موجود
        # (آیکون گرد رنگی بر اساس دسته‌بندی گیاه) بلافاصله و تمیز فعال
        # می‌شود — دقیقاً همان چیزی که برای گیاهان سفارشی بدون عکس واقعی
        # مناسب است.
        plant_data.setdefault('image', '')
        self.all_plants.append(plant_data)
        
        try:
            existing = []
            if self.custom_plants_store.exists('plants'):
                existing = self.custom_plants_store.get('plants')['data']
            existing.append(plant_data)
            self.custom_plants_store.put('plants', data=existing)
        except Exception as e:
            print(f"خطا در ذخیره گیاه: {e}")
    
    def go_to_screen(self, screen_name, direction='left'):
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = screen_name
    
    def go_back(self):
        self.screen_manager.transition.direction = 'right'
        self.screen_manager.current = 'home'
    
    def show_plant_detail(self, plant_id):
        plant = self._get_plant_by_id(plant_id) if self._get_plant_by_id else None
        if not plant:

            for p in self.all_plants:
                if p['id'] == plant_id:
                    plant = p
                    break
        
        if plant:
            self.current_plant = plant
            detail_screen = self.screen_manager.get_screen('plant_detail')
            detail_screen.load_plant(plant)
            self.go_to_screen('plant_detail')
    
    def on_start(self):
        print("🌱 گیاهیار راه‌اندازی شد!")

        Clock.schedule_interval(self.check_timers, 60)
    
    def check_timers(self, dt):
        try:


            fresh_store = JsonStore('timers_data.json')
            if fresh_store.exists('timers'):
                timers = fresh_store.get('timers')['data']
                now = datetime.now()
                for timer in timers:
                    if timer.get('active') and timer.get('next_time'):
                        next_time = datetime.fromisoformat(timer['next_time'])
                        if now >= next_time:
                            self.show_timer_notification(timer['name'])
        except Exception as e:
            print(f"خطا در چک تایمر: {e}")
    
    def show_timer_notification(self, timer_name):
        popup_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        with popup_content.canvas.before:
            Color(*COLORS['card'])
            _tn_bg = Rectangle(pos=popup_content.pos, size=popup_content.size)
        popup_content.bind(pos=lambda i, v: setattr(_tn_bg, 'pos', v),
                           size=lambda i, v: setattr(_tn_bg, 'size', v))

        icon_label = Image(source=icon_path('ic_clock'), size_hint_y=None,
                           height=dp(60), allow_stretch=True, keep_ratio=True)
        title = Label(
            text=f'زمان: {timer_name}!',
            font_size=sp(18),
            bold=True,
            color=COLORS['primary'],
        )
        msg = Label(
            text='وقت مراقبت از گیاهتان رسیده است',
            font_size=sp(14),
            color=COLORS['text_secondary'],
        )
        
        ok_btn = Button(
            text='باشه',
            size_hint_y=None,
            height=dp(45),
            background_color=COLORS['primary'],
            color=COLORS['white'],
        )
        
        popup_content.add_widget(icon_label)
        popup_content.add_widget(title)
        popup_content.add_widget(msg)
        popup_content.add_widget(ok_btn)
        
        popup = Popup(
            title=rtl('یادآوری گیاه'),
            content=popup_content,
            size_hint=(0.85, 0.4),
            auto_dismiss=False,
        )
        
        ok_btn.bind(on_press=lambda x: popup.dismiss())
        popup.open()


if __name__ == '__main__':
    PlantCareApp().run()

