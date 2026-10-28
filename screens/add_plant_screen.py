from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.ui_components import COLORS, AdBanner, GreenButton, icon_path, PersianTextInput, theme_hex
from utils.helpers import rtl


class AddPlantScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        # مقدار واقعیِ (بدون‌ریشیپ) هر Spinner جدا از خودِ ویجت نگه داشته
        # می‌شود — دلیل را بالای _make_spinner_field ببینید.
        self._spinner_values = {}
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt):
        root = FloatLayout()
        with root.canvas.before:
            Color(*COLORS['background'])
            bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(bg, 'pos', v),
                  size=lambda i, v: setattr(bg, 'size', v))


        header = BoxLayout(orientation='horizontal', size_hint=(1, None),
                           height=dp(60), padding=[dp(10), dp(8)], spacing=dp(8),
                           pos_hint={'top': 1})
        with header.canvas.before:
            Color(*COLORS['primary'])
            hbg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(hbg, 'pos', v),
                    size=lambda i, v: setattr(hbg, 'size', v))
        back_btn = Button(text='←', font_size=sp(22), size_hint=(None, 1),
                          width=dp(44), background_normal='',
                          background_color=[0, 0, 0, 0], color=COLORS['white'])
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('plant_list', 'right'))
        header.add_widget(back_btn)
        header.add_widget(Image(source=icon_path('ic_plus_white'), size_hint=(None, 1),
                                width=dp(20), allow_stretch=True, keep_ratio=True))
        header.add_widget(Label(text='افزودن گیاه جدید', font_size=sp(18),
                                bold=True, color=COLORS['white'], halign='right'))

        scroll = ScrollView(size_hint=(1, None), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None,
                            spacing=dp(10), padding=[dp(14), dp(14)])
        content.bind(minimum_height=content.setter('height'))
        scroll.bind(width=content.setter('width'))

        icon_box = BoxLayout(size_hint_y=None, height=dp(80))
        icon_box.add_widget(Widget())
        icon_box.add_widget(Image(source=icon_path('ic_leaf'), size_hint=(None, 1),
                                  width=dp(70), allow_stretch=True, keep_ratio=True))
        icon_box.add_widget(Widget())
        content.add_widget(icon_box)


        fields = [
            ('نام فارسی گیاه *', 'مثلاً: سانسوریا', 'name', False),
            ('نام علمی', 'مثلاً: Sansevieria trifasciata', 'scientific_name', False),
            ('توضیحات', 'توضیح مختصری درباره گیاه...', 'description', True),
            ('شرایط رشد', 'نور، دما، رطوبت...', 'growth_conditions', True),
            ('مشکلات رایج', 'بیماری‌ها، آفات...', 'common_problems', True),
            ('روش درمان', 'نحوه رفع مشکلات...', 'treatment', True),
        ]
        self._inputs = {}
        for label, hint, key, multiline in fields:
            content.add_widget(self._make_field(label, hint, key, multiline))


        spinners_data = [
            ('دسته‌بندی', 'category', ['آپارتمانی', 'گلدار', 'دارویی', 'درخت میوه']),
            ('نیاز به نور', 'light', ['کم', 'متوسط', 'زیاد', 'کم تا متوسط', 'متوسط تا زیاد']),
            ('میزان آبیاری', 'watering', ['کم', 'متوسط', 'زیاد', 'کم تا متوسط']),
            ('سطح نگهداری', 'care_level', ['بسیار آسان', 'آسان', 'متوسط', 'سخت']),
            ('محدوده قیمت', 'price_range', ['ارزان', 'مناسب', 'نسبتاً گران', 'گران']),
        ]
        for label, key, values in spinners_data:
            content.add_widget(self._make_spinner_field(label, key, values))


        save_btn = GreenButton(text='ذخیره گیاه')
        save_btn.bind(on_press=self._save_plant)
        content.add_widget(save_btn)
        content.add_widget(Widget(size_hint_y=None, height=dp(20)))

        scroll.add_widget(content)
        ad = AdBanner(size_hint=(None, None), size=(dp(300), dp(30)),
                      pos_hint={'center_x': 0.5})

        root.add_widget(scroll)
        root.add_widget(header)
        root.add_widget(ad)
        self.add_widget(root)

        def _fix(*a):
            avail_h = max(dp(120), self.height - dp(60) - dp(30))
            scroll.pos = (0, dp(30))
            scroll.height = avail_h
            scroll.width = self.width
            content.width = scroll.width
            ad.pos = (self.width / 2 - dp(150), 0)
        self._fix_layout = _fix
        Clock.schedule_once(_fix, 0.05)
        # همان دلیلِ tools_screen.py: یک اجرای یک‌باره ممکن است با
        # self.width/height هنوز-نهایی‌نشده محاسبه شود و برای همیشه فرم را
        # نامرئی/بسیار باریک نگه دارد (دقیقاً چیزی که در اسکرین‌شات گوشی
        # دیده شد). این دو خط تضمین می‌کنند هر وقت اندازه‌ی واقعی مشخص شد
        # (چه با تغییر اندازه، چه در لحظه‌ی ورود واقعی به صفحه)، دوباره با
        # مقادیر درست محاسبه شود.
        self.bind(size=_fix)

    def on_enter(self):
        if getattr(self, '_fix_layout', None):
            self._fix_layout()

    def _make_field(self, label_text, hint, key, multiline):
        outer = BoxLayout(orientation='vertical', size_hint_y=None,
                          height=dp(90) if multiline else dp(72), spacing=dp(4))
        lbl = Label(text=label_text, font_size=sp(13), color=COLORS['text_primary'],
                    size_hint_y=None, height=dp(24), halign='right')
        lbl.bind(size=lbl.setter('text_size'))

        inp = PersianTextInput(
            hint_text=hint, font_size=sp(13), multiline=multiline,
            size_hint_y=None, height=dp(60) if multiline else dp(42),
            background_color=theme_hex('#F1F8E9'),
            foreground_color=COLORS['text_dark'],
            hint_text_color=theme_hex('#A5D6A7'),
            halign='right',
        )
        self._inputs[key] = inp
        outer.add_widget(lbl)
        outer.add_widget(inp)
        return outer

    def _make_spinner_field(self, label_text, key, values):
        outer = BoxLayout(orientation='vertical', size_hint_y=None,
                          height=dp(68), spacing=dp(4))
        lbl = Label(text=label_text, font_size=sp(13), color=COLORS['text_primary'],
                    size_hint_y=None, height=dp(24), halign='right')
        lbl.bind(size=lbl.setter('text_size'))
        sp_widget = Spinner(text=values[0], values=values, size_hint_y=None,
                            height=dp(40), background_color=COLORS['primary'],
                            color=COLORS['white'])

        # نکته‌ی مهم: Spinner در کیوی زیرکلاسِ Button است و Button خودش
        # زیرکلاسِ Label است، پس همان پچ RTL که در main.py برای فارسی‌نویسی
        # روی Label.__init__ زده شده، روی متنِ اولیه‌ی Spinner هم اعمال
        # می‌شود (چه مقدار پیش‌فرض، چه گزینه‌ای که کاربر از منو انتخاب
        # می‌کند — چون آن گزینه‌ها هم داخلی با همان __init__ ساخته می‌شوند).
        # یعنی sp_widget.text همیشه نسخه‌ی ریشیپ‌شده/بازچینی‌شده برای نمایش
        # راست‌به‌چپ است، نه مقدار خام. اگر مستقیم همین را ذخیره کنیم (کاری
        # که قبلاً در _save_plant انجام می‌شد)، category/light/watering/...
        # با یک رشته‌ی درهم‌ریخته که با هیچ‌جای دیگر برنامه مطابقت ندارد
        # ذخیره می‌شد. راه‌حل: نگاشتِ معکوسِ «متنِ ریشیپ‌شده → مقدار خام» را
        # یک‌بار می‌سازیم و هر بار Spinner عوض شد، مقدار واقعی را در
        # self._spinner_values کنار خودِ ویجت نگه می‌داریم.
        rtl_to_raw = {rtl(v): v for v in values}
        self._spinner_values[key] = values[0]

        def _on_spinner_text(instance, new_text, k=key, mapping=rtl_to_raw):
            self._spinner_values[k] = mapping.get(new_text, new_text)
        sp_widget.bind(text=_on_spinner_text)

        self._inputs[key] = sp_widget
        outer.add_widget(lbl)
        outer.add_widget(sp_widget)
        return outer

    def _save_plant(self, instance):
        name = ''
        if 'name' in self._inputs:
            w = self._inputs['name']
            name = w.raw_text.strip() if hasattr(w, 'raw_text') else w.text.strip()

        if not name:
            _err_box = BoxLayout(padding=dp(16))
            with _err_box.canvas.before:
                Color(*COLORS['card'])
                _err_bg = Rectangle(pos=_err_box.pos, size=_err_box.size)
            _err_box.bind(pos=lambda i, v: setattr(_err_bg, 'pos', v),
                         size=lambda i, v: setattr(_err_bg, 'size', v))
            _err_box.add_widget(Label(text='نام گیاه را وارد کنید!', color=COLORS['error']))
            popup = Popup(
                title=rtl('خطا'),
                content=_err_box,
                size_hint=(0.7, 0.25),
            )
            popup.open()
            return

        plant_data = {}
        for key, widget in self._inputs.items():
            if key in self._spinner_values:
                # مقدار واقعیِ Spinner، نه widget.text (که ریشیپ‌شده و
                # برای ذخیره نامعتبر است — توضیح کامل در _make_spinner_field)
                plant_data[key] = self._spinner_values[key]
            elif hasattr(widget, 'raw_text'):
                # PersianTextInput: raw_text مقدار خام/واقعی تایپ‌شده است،
                # نه widget.text که نسخه‌ی ریشیپ‌شده برای نمایش است
                plant_data[key] = widget.raw_text.strip()
            elif hasattr(widget, 'text'):
                plant_data[key] = widget.text.strip()

        plant_data.setdefault('suitable_for', 'خانه، آپارتمان')
        plant_data.setdefault('special_features', '')
        plant_data.setdefault('air', 'نرمال')
        plant_data['watering_days'] = 7
        plant_data['fertilizing_days'] = 30

        if self.app:
            # add_custom_plant مقدار plant_data['id'] را همین‌جا، روی همین
            # دیکشنری، ست می‌کند؛ پس بعد از این خط plant_data['id'] معتبر است.
            self.app.add_custom_plant(plant_data)

        self._reset_form()

        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))
        with content.canvas.before:
            Color(*COLORS['card'])
            _sc_bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda i, v: setattr(_sc_bg, 'pos', v),
                    size=lambda i, v: setattr(_sc_bg, 'size', v))
        content.add_widget(Image(source=icon_path('ic_check'), size_hint_y=None,
                                 height=dp(36), allow_stretch=True, keep_ratio=True))
        content.add_widget(Label(text='گیاه با موفقیت اضافه شد!',
                                 font_size=sp(15), color=COLORS['primary'],
                                 halign='center'))
        ok_btn = Button(text='مشاهده گیاه', size_hint_y=None, height=dp(44),
                        background_color=COLORS['primary'], color=COLORS['white'])
        content.add_widget(ok_btn)
        popup = Popup(title=rtl('موفقیت'), content=content,
                      size_hint=(0.8, 0.32), auto_dismiss=False)

        new_id = plant_data.get('id')

        def _go_view(x):
            popup.dismiss()
            # رفتن مستقیم به صفحه‌ی خودِ گیاهِ تازه‌ساخته‌شده، نه لیست کلی
            # ۸۰+ تایی — تا کاربر بلافاصله و بی‌ابهام ببیند که واقعاً ذخیره
            # شده، به‌جای این‌که در ابتدای لیست فرود بیاید و گیاه تازه را
            # (که انتهای لیست اضافه می‌شود) نبیند و فکر کند کاری انجام نشده.
            if new_id is not None:
                self.app.show_plant_detail(new_id)
            else:
                self.app.go_to_screen('plant_list')

        ok_btn.bind(on_press=_go_view)
        popup.open()

    def _reset_form(self):
        """فرم را برای افزودن گیاه بعدی خالی می‌کند. چون _build_ui فقط
        یک‌بار (هنگام ساخت صفحه) اجرا می‌شود، بدون این متد، بازگشت به این
        صفحه برای افزودن گیاه دوم، مقادیر گیاه قبلی را نگه می‌داشت."""
        for widget in self._inputs.values():
            if hasattr(widget, 'raw_text'):
                widget.raw_text = ''
            elif isinstance(widget, TextInput):
                widget.text = ''
            elif isinstance(widget, Spinner):
                # با rtl() ست می‌شود (نه مقدار خام) چون این‌جا از طریق
                # __init__ رد نمی‌شویم و پچِ RTL خودکار اعمال نمی‌شود؛
                # هندلر متصل‌شده به bind(text=...) خودش self._spinner_values
                # را هم به مقدار خامِ متناظر برمی‌گرداند.
                widget.text = rtl(widget.values[0]) if widget.values else widget.text

