from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.ui_components import COLORS, AdBanner, GreenButton, BottomNavBar, icon_path, PersianTextInput, theme_hex
from utils.helpers import relative_time_fa, rtl


class TimerScreen(Screen):
    MAX_TIMERS = 100
    MAX_DAYS = 30
    MAX_HOURS = 23

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.store = JsonStore('timers_data.json')
        self.timers = []
        self._list_layout = None
        self._count_label = None

        # وضعیت موقت فرم «افزودن تایمر» (فقط وقتی پاپ‌آپ باز است معنا دارد)
        self._draft = {'days': 7, 'hours': 0}
        self._day_value_lbl = None
        self._hour_value_lbl = None
        self._duration_preview = None
        self._timer_type_value = None

        self._load_timers()
        Clock.schedule_once(self._build_ui, 0)

    def _load_timers(self):
        try:
            if self.store.exists('timers'):
                self.timers = self.store.get('timers')['data']
        except Exception:
            self.timers = []

    def _save_timers(self):
        try:
            self.store.put('timers', data=self.timers)
        except Exception as e:
            print(f'خطا در ذخیره تایمر: {e}')

    # ------------------------------------------------------------------
    # ساخت رابط اصلی صفحه
    # ------------------------------------------------------------------
    def _build_ui(self, dt):
        root = FloatLayout()
        with root.canvas.before:
            Color(*COLORS['background'])
            bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(bg, 'pos', v),
                  size=lambda i, v: setattr(bg, 'size', v))

        # --- هدر ---
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
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('tools', 'right'))
        header.add_widget(back_btn)
        header.add_widget(Image(source=icon_path('ic_clock_white'), size_hint=(None, 1),
                                 width=dp(24), allow_stretch=True, keep_ratio=True))
        header.add_widget(Label(text='تایمر مراقبت', font_size=sp(20),
                                bold=True, color=COLORS['white'], halign='right'))

        # --- دکمه‌ی برجسته‌ی «افزودن تایمر جدید» (ثابت، بالای صفحه) ---
        add_row = BoxLayout(orientation='horizontal', size_hint=(1, None),
                            height=dp(62), padding=[dp(14), dp(6)])
        add_new_btn = GreenButton(text='افزودن تایمر جدید')
        add_new_btn.bind(on_press=lambda x: self._show_add_popup())
        add_row.add_widget(add_new_btn)

        # --- نوار تعداد تایمرها ---
        info_bar = BoxLayout(size_hint=(1, None), height=dp(36),
                             padding=[dp(14), dp(4)])
        with info_bar.canvas.before:
            Color(*theme_hex('#E8F5E9'))
            ibbg = Rectangle(pos=info_bar.pos, size=info_bar.size)
        info_bar.bind(pos=lambda i, v: setattr(ibbg, 'pos', v),
                      size=lambda i, v: setattr(ibbg, 'size', v))

        self._count_label = Label(
            text=f'تعداد تایمر: {len(self.timers)} / {self.MAX_TIMERS}',
            font_size=sp(12), color=COLORS['text_secondary'],
            halign='right',
        )
        self._count_label.bind(size=self._count_label.setter('text_size'))
        info_bar.add_widget(self._count_label)

        # --- لیست قابل‌اسکرول تایمرها ---
        scroll = ScrollView(size_hint=(1, None), do_scroll_x=False)
        self._list_layout = BoxLayout(orientation='vertical', size_hint_y=None,
                                      spacing=dp(8), padding=[dp(12), dp(10)])
        self._list_layout.bind(minimum_height=self._list_layout.setter('height'))
        scroll.add_widget(self._list_layout)
        # ScrollView عرض size_hint_x فرزندش را خودکار به پیکسل واقعی تبدیل
        # نمی‌کند (چون خودش یک Layout به آن معنا نیست)؛ بدون این خط، لیست
        # تایمرها روی عرض پیش‌فرض کوچک کیوی می‌ماند و عملاً نامرئی می‌شود —
        # همان مشکلی که در ToolsScreen باعث خالی دیده‌شدن صفحه شده بود.
        scroll.bind(width=self._list_layout.setter('width'))

        nav = BottomNavBar(app_ref=self.app, active_tab='tools')
        nav.pos_hint = {'x': 0, 'y': 0}
        ad = AdBanner(size_hint=(None, None), size=(dp(300), dp(30)),
                      pos_hint={'center_x': 0.5})

        root.add_widget(scroll)
        root.add_widget(header)
        root.add_widget(add_row)
        root.add_widget(info_bar)
        root.add_widget(ad)
        root.add_widget(nav)
        self.add_widget(root)

        def _fix(*a):
            header_h = dp(60)
            add_h = dp(62)
            info_h = dp(36)
            nav_h = dp(60)
            ad_h = dp(30)
            avail_h = max(dp(120), self.height - header_h - add_h - info_h - nav_h - ad_h)
            add_row.pos = (0, self.height - header_h - add_h)
            info_bar.pos = (0, self.height - header_h - add_h - info_h)
            scroll.pos = (0, nav_h + ad_h)
            scroll.height = avail_h
            scroll.width = self.width
            self._list_layout.width = scroll.width
            ad.pos = (self.width / 2 - dp(150), nav_h)
        self._fix_layout = _fix
        Clock.schedule_once(_fix, 0.05)
        # همان مشکلِ tools_screen.py/add_plant_screen.py: بدون این، اگر
        # اولین اجرا self.height/width هنوز-نهایی‌نشده را ببیند (وقتی این
        # صفحه تازه ساخته شده ولی هنوز صفحه‌ی *فعال* نیست)، لیست تایمرها
        # برای همیشه نامرئی/بسیار باریک می‌ماند.
        self.bind(size=_fix)
        self._render_timers()

    # ------------------------------------------------------------------
    # نمایش لیست تایمرها
    # ------------------------------------------------------------------
    def _render_timers(self):
        if not self._list_layout:
            return
        self._list_layout.clear_widgets()

        if not self.timers:
            empty_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                  height=dp(230), padding=[dp(30), dp(16)], spacing=dp(12))
            icon_wrap = BoxLayout(size_hint_y=None, height=dp(64))
            icon_wrap.add_widget(Widget())
            icon_wrap.add_widget(Image(source=icon_path('ic_clock'), size_hint=(None, None),
                                       size=(dp(64), dp(64)), allow_stretch=True, keep_ratio=True))
            icon_wrap.add_widget(Widget())
            empty_box.add_widget(icon_wrap)
            empty_box.add_widget(Label(
                text='هنوز تایمری ندارید!\nبرای اولین تایمر، دکمه «افزودن تایمر جدید» را در بالای صفحه بزنید.',
                font_size=sp(14), color=COLORS['text_secondary'],
                halign='center',
            ))
            self._list_layout.add_widget(empty_box)
        else:
            for i, timer in enumerate(self.timers):
                card = self._make_timer_card(timer, i)
                self._list_layout.add_widget(card)

        if self._count_label:
            self._count_label.text = rtl(f'تعداد تایمر: {len(self.timers)} / {self.MAX_TIMERS}')

    def _make_timer_card(self, timer, idx):
        is_active = timer.get('active', True)
        bg_color = theme_hex('#E8F5E9') if is_active else theme_hex('#F5F5F5')
        title_color = COLORS['primary'] if is_active else theme_hex('#9E9E9E')

        card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(95),
                         padding=[dp(14), dp(10)], spacing=dp(6))
        with card.canvas.before:
            Color(*bg_color)
            cbg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda i, v: setattr(cbg, 'pos', v),
                  size=lambda i, v: setattr(cbg, 'size', v))

        row1 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
        name_lbl = Label(
            text=timer.get('name', 'بی‌نام'),
            font_size=sp(15), bold=True, color=title_color,
            halign='right', valign='middle',
        )
        name_lbl.bind(size=name_lbl.setter('text_size'))

        status_lbl = Label(
            text='فعال' if is_active else 'متوقف',
            font_size=sp(11),
            color=COLORS['primary'] if is_active else theme_hex('#9E9E9E'),
            size_hint=(None, 1), width=dp(75),
        )
        row1.add_widget(name_lbl)
        row1.add_widget(status_lbl)


        row2 = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(22),
                         spacing=dp(10))
        interval_days = timer.get('interval_days', 7)
        interval_hours = timer.get('interval_hours', 0)
        next_time = timer.get('next_time', '')
        if next_time:
            next_text = f'بعدی: {relative_time_fa(next_time)}'
        else:
            next_text = 'تنظیم نشده'
        timer_type = timer.get('timer_type', 'سایر')

        info_lbl = Label(
            text=f'{timer_type}  |  {self._format_duration(interval_days, interval_hours)}  |  {next_text}',
            font_size=sp(11), color=COLORS['text_secondary'],
            halign='right',
        )
        info_lbl.bind(size=info_lbl.setter('text_size'))
        row2.add_widget(info_lbl)


        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(28), spacing=dp(8))
        btn_row.add_widget(Widget())

        del_btn = Button(
            text='حذف', font_size=sp(11), size_hint=(None, 1), width=dp(70),
            background_normal='', background_color=theme_hex('#FFEBEE'),
            color=theme_hex('#C62828'),
        )
        _idx = idx
        del_btn.bind(on_press=lambda x, i=_idx: self._delete_timer(i))

        toggle_btn = Button(
            text='توقف' if is_active else 'فعال‌سازی',
            font_size=sp(11), size_hint=(None, 1), width=dp(90),
            background_normal='',
            background_color=theme_hex('#E3F2FD'),
            color=theme_hex('#1565C0'),
        )
        toggle_btn.bind(on_press=lambda x, i=_idx: self._toggle_timer(i))

        btn_row.add_widget(del_btn)
        btn_row.add_widget(toggle_btn)

        card.add_widget(row1)
        card.add_widget(row2)
        card.add_widget(btn_row)
        return card

    # ------------------------------------------------------------------
    # کمکی‌های نمایش مدت‌زمان
    # ------------------------------------------------------------------
    def _format_duration(self, days, hours):
        """متن فارسیِ مدت‌زمان شمارش‌معکوس را از روی روز/ساعت می‌سازد، مثلاً
        'هر 7 روز' یا 'هر 2 روز و 5 ساعت' یا 'هر 3 ساعت'."""
        parts = []
        if days > 0:
            parts.append(f'{days} روز')
        if hours > 0 or not parts:
            parts.append(f'{hours} ساعت')
        return 'هر ' + ' و '.join(parts)

    def _field_label(self, text):
        lbl = Label(text=text, font_size=sp(14), color=COLORS['text_primary'],
                    size_hint_y=None, height=dp(26), halign='right', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        return lbl

    # ------------------------------------------------------------------
    # ردیف افزایش/کاهش (استپر) برای روز یا ساعت
    # ------------------------------------------------------------------
    def _make_stepper_row(self, label_text, key):
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48),
                        spacing=dp(10))

        lbl = Label(text=label_text, font_size=sp(14), bold=True,
                    color=COLORS['text_primary'], size_hint=(None, 1), width=dp(56),
                    halign='right', valign='middle')
        lbl.bind(size=lbl.setter('text_size'))
        row.add_widget(lbl)
        row.add_widget(Widget())

        minus_btn = Button(
            text='-', font_size=sp(24), bold=True,
            size_hint=(None, None), size=(dp(44), dp(44)),
            background_normal='', background_color=COLORS['secondary'],
            color=COLORS['white'],
        )
        value_lbl = Label(
            text=str(self._draft[key]), font_size=sp(17), bold=True,
            color=COLORS['text_dark'], size_hint=(None, 1), width=dp(60),
            halign='center', valign='middle',
        )
        value_lbl.bind(size=value_lbl.setter('text_size'))
        plus_btn = Button(
            text='+', font_size=sp(22), bold=True,
            size_hint=(None, None), size=(dp(44), dp(44)),
            background_normal='', background_color=COLORS['primary'],
            color=COLORS['white'],
        )

        if key == 'days':
            self._day_value_lbl = value_lbl
        else:
            self._hour_value_lbl = value_lbl

        # نکته: 'k=key' آرگومان پیش‌فرض لازم است تا مقدار همین لحظه لمس
        # (capture) شود، نه اینکه با ارجاع به متغیر بیرونی گره بخورد (همان
        # اشتباهی که در BottomNavBar پیش‌تر اصلاح شد).
        minus_btn.bind(on_press=lambda inst, k=key: self._adjust_draft(k, -1))
        plus_btn.bind(on_press=lambda inst, k=key: self._adjust_draft(k, 1))

        row.add_widget(minus_btn)
        row.add_widget(value_lbl)
        row.add_widget(plus_btn)
        return row

    def _adjust_draft(self, key, delta):
        if key == 'hours':
            # اگر روز صفر باشد، حداقل ساعت باید ۱ بماند (کمینه‌ی کل تایمر
            # همان یک ساعت است)؛ در غیر این صورت ساعت می‌تواند صفر هم بشود.
            floor = 1 if self._draft['days'] == 0 else 0
            new_val = self._draft['hours'] + delta
            if floor <= new_val <= self.MAX_HOURS:
                self._draft['hours'] = new_val
        else:
            new_val = self._draft['days'] + delta
            if 0 <= new_val <= self.MAX_DAYS:
                self._draft['days'] = new_val
                # اگر با کم کردن روز به صفر رسیدیم و ساعت هم صفر بود،
                # ساعت را به حداقل مجاز (۱) برمی‌گردانیم.
                if self._draft['days'] == 0 and self._draft['hours'] == 0:
                    self._draft['hours'] = 1

        if self._day_value_lbl:
            self._day_value_lbl.text = rtl(str(self._draft['days']))
        if self._hour_value_lbl:
            self._hour_value_lbl.text = rtl(str(self._draft['hours']))
        if self._duration_preview:
            self._duration_preview.text = rtl(
                self._format_duration(self._draft['days'], self._draft['hours'])
            )

    # ------------------------------------------------------------------
    # فرم افزودن تایمر جدید
    # ------------------------------------------------------------------
    def _show_add_popup(self):
        if len(self.timers) >= self.MAX_TIMERS:
            self._show_message('محدودیت', f'حداکثر {self.MAX_TIMERS} تایمر می‌توانید داشته باشید.')
            return

        self._draft = {'days': 7, 'hours': 0}
        self._day_value_lbl = None
        self._hour_value_lbl = None

        popup_content = BoxLayout(orientation='vertical', spacing=dp(12),
                                  padding=[dp(16), dp(14)])
        # Popup پیش‌فرض کیوی پس‌زمینه‌ی تیره دارد؛ بدون این پس‌زمینه‌ی روشن،
        # متن‌های تیره (رنگ‌های text_dark/text_primary) روی آن تیرگی تقریباً
        # نامرئی می‌شوند — دقیقاً همان چیزی که در اسکرین‌شات دیده شد.
        with popup_content.canvas.before:
            Color(*COLORS['card'])
            _pc_bg = Rectangle(pos=popup_content.pos, size=popup_content.size)
        popup_content.bind(pos=lambda i, v: setattr(_pc_bg, 'pos', v),
                           size=lambda i, v: setattr(_pc_bg, 'size', v))

        form_scroll = ScrollView(size_hint=(1, 1), bar_width=dp(3), do_scroll_x=False)
        form = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))
        form_scroll.bind(width=form.setter('width'))

        # نام تایمر
        form.add_widget(self._field_label('نام تایمر:'))
        name_input = PersianTextInput(
            hint_text='مثلاً: آبیاری مونسترا',
            font_size=sp(14), multiline=False,
            size_hint_y=None, height=dp(44),
            background_color=theme_hex('#F1F8E9'),
            halign='right',
        )
        form.add_widget(name_input)

        # نوع مراقبت
        form.add_widget(self._field_label('نوع مراقبت:'))
        type_values = ['آبیاری', 'کود دادن', 'تعویض خاک', 'هرس', 'سم‌پاشی', 'سایر']
        type_spinner = Spinner(
            text=type_values[0],
            values=type_values,
            size_hint_y=None, height=dp(44),
            background_color=COLORS['primary'],
            color=COLORS['white'],
        )
        # Spinner زیرکلاسِ Button/Label است، پس متنِ اولیه و گزینه‌های داخل
        # منو هم از همان پچ RTL (بالای main.py) می‌گذرند و widget.text مقدار
        # ریشیپ‌شده/بازچینی‌شده برای نمایش است، نه مقدار خام — دقیقاً همان
        # باگی که در add_plant_screen.py برای دسته‌بندی/نور/آبیاری/... پیدا
        # و رفع شد. این‌جا هم با یک نگاشتِ معکوس، مقدار واقعیِ نوع مراقبت را
        # کنار خودش نگه می‌داریم تا در self._save_new_timer از widget.text
        # خراب استفاده نشود.
        self._timer_type_value = type_values[0]
        _type_rtl_to_raw = {rtl(v): v for v in type_values}

        def _on_type_change(instance, new_text, mapping=_type_rtl_to_raw):
            self._timer_type_value = mapping.get(new_text, new_text)
        type_spinner.bind(text=_on_type_change)
        form.add_widget(type_spinner)

        # مدت زمان شمارش معکوس (روز + ساعت) — با دکمه‌های افزایش/کاهش
        form.add_widget(self._field_label('مدت زمان شمارش معکوس:'))

        day_row = self._make_stepper_row('روز', 'days')
        hour_row = self._make_stepper_row('ساعت', 'hours')
        form.add_widget(day_row)
        form.add_widget(hour_row)

        self._duration_preview = Label(
            text=self._format_duration(self._draft['days'], self._draft['hours']),
            font_size=sp(13), bold=True, color=COLORS['primary'],
            size_hint_y=None, height=dp(26), halign='center', valign='middle',
        )
        self._duration_preview.bind(size=self._duration_preview.setter('text_size'))
        form.add_widget(self._duration_preview)

        hint_lbl = Label(
            text='حداقل مدت زمان 1 ساعت و حداکثر 30 روز و 23 ساعت است.',
            font_size=sp(10.5), color=COLORS['text_secondary'],
            size_hint_y=None, height=dp(30), halign='center', valign='middle',
        )
        hint_lbl.bind(size=hint_lbl.setter('text_size'))
        form.add_widget(hint_lbl)

        form_scroll.add_widget(form)
        popup_content.add_widget(form_scroll)

        btn_row = BoxLayout(orientation='horizontal', spacing=dp(10),
                            size_hint_y=None, height=dp(48))
        cancel_btn = Button(text='انصراف', font_size=sp(14),
                            background_color=theme_hex('#BDBDBD'),
                            color=COLORS['white'])
        save_btn = Button(text='ذخیره', font_size=sp(14),
                          background_color=COLORS['primary'],
                          color=COLORS['white'])
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(save_btn)
        popup_content.add_widget(btn_row)

        popup = Popup(
            title=rtl('افزودن تایمر جدید'),
            content=popup_content,
            size_hint=(0.92, 0.88),
            auto_dismiss=False,
        )

        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        save_btn.bind(on_press=lambda x: self._save_new_timer(
            popup, name_input.raw_text, self._timer_type_value
        ))
        popup.open()

    def _save_new_timer(self, popup, name, timer_type):
        name = name.strip()
        if not name:
            self._show_message('نام لازم است', 'لطفاً یک نام برای تایمر وارد کنید.')
            return

        # کلمپ دفاعی؛ رابط کاربری همین بازه را تضمین می‌کند ولی این خط
        # تضمین دوم است تا داده‌ی ذخیره‌شده همیشه معتبر بماند.
        days = max(0, min(self.MAX_DAYS, self._draft.get('days', 0)))
        hours = max(0, min(self.MAX_HOURS, self._draft.get('hours', 1)))
        if days == 0 and hours == 0:
            hours = 1

        next_time = (datetime.now() + timedelta(days=days, hours=hours)).isoformat()
        new_timer = {
            'id': len(self.timers) + 1,
            'name': name,
            'timer_type': timer_type,
            'interval_days': days,
            'interval_hours': hours,
            'next_time': next_time,
            'active': True,
            'created': datetime.now().isoformat(),
        }
        self.timers.append(new_timer)
        self._save_timers()
        popup.dismiss()
        self._render_timers()

    def _delete_timer(self, idx):
        def _confirm(popup):
            if 0 <= idx < len(self.timers):
                self.timers.pop(idx)
                self._save_timers()
                self._render_timers()
            popup.dismiss()

        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        with content.canvas.before:
            Color(*COLORS['card'])
            _dc_bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda i, v: setattr(_dc_bg, 'pos', v),
                    size=lambda i, v: setattr(_dc_bg, 'size', v))
        content.add_widget(Label(text='آیا مطمئن هستید؟', font_size=sp(15),
                                 color=COLORS['text_dark']))
        btn_row = BoxLayout(orientation='horizontal', spacing=dp(10),
                            size_hint_y=None, height=dp(44))
        no_btn = Button(text='خیر', background_color=theme_hex('#BDBDBD'),
                        color=COLORS['white'])
        yes_btn = Button(text='بله، حذف شود', background_color=COLORS['error'],
                         color=COLORS['white'])
        btn_row.add_widget(no_btn)
        btn_row.add_widget(yes_btn)
        content.add_widget(btn_row)

        popup = Popup(title=rtl('حذف تایمر'), content=content,
                      size_hint=(0.8, 0.3), auto_dismiss=False)
        no_btn.bind(on_press=lambda x: popup.dismiss())
        yes_btn.bind(on_press=lambda x: _confirm(popup))
        popup.open()

    def _toggle_timer(self, idx):
        if 0 <= idx < len(self.timers):
            self.timers[idx]['active'] = not self.timers[idx].get('active', True)
            self._save_timers()
            self._render_timers()

    def _show_message(self, title, msg):
        content = BoxLayout(orientation='vertical', padding=dp(16))
        with content.canvas.before:
            Color(*COLORS['card'])
            _mc_bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda i, v: setattr(_mc_bg, 'pos', v),
                    size=lambda i, v: setattr(_mc_bg, 'size', v))
        content.add_widget(Label(text=msg, font_size=sp(14),
                                 color=COLORS['text_dark'], halign='center'))
        ok_btn = Button(text='باشه', size_hint_y=None, height=dp(44),
                        background_color=COLORS['primary'], color=COLORS['white'])
        content.add_widget(ok_btn)
        popup = Popup(title=rtl(title), content=content,
                      size_hint=(0.8, 0.3), auto_dismiss=True)
        ok_btn.bind(on_press=lambda x: popup.dismiss())
        popup.open()

    def on_enter(self):
        if getattr(self, '_fix_layout', None):
            self._fix_layout()
        self._load_timers()
        self._render_timers()
