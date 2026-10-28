from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.ui_components import (COLORS, PLANT_CATEGORY_COLORS, AdBanner,
                                       PlantCard, SectionTitle, BottomNavBar, icon_path)
from data.plants_db import PLANTS_DATA, CATEGORIES


class PlantListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.active_filter = 'همه'
        self.search_query = ''
        self._plant_list_layout = None
        self._filter_btns = {}
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt):
        root = FloatLayout()
        with root.canvas.before:
            Color(*COLORS['background'])
            bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(bg, 'pos', v),
                  size=lambda i, v: setattr(bg, 'size', v))


        header = self._build_header()
        header.pos_hint = {'top': 1, 'x': 0}


        filter_bar = self._build_filter_bar()


        self._scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self._plant_list_layout = BoxLayout(
            orientation='vertical', size_hint_y=None,
            spacing=dp(6), padding=[dp(12), dp(8)]
        )
        self._plant_list_layout.bind(minimum_height=self._plant_list_layout.setter('height'))
        self._scroll.add_widget(self._plant_list_layout)
        self._scroll.bind(width=self._plant_list_layout.setter('width'))


        nav = BottomNavBar(app_ref=self.app, active_tab='plant_list')
        nav.pos_hint = {'x': 0, 'y': 0}


        ad = AdBanner(size_hint=(None, None), size=(dp(300), dp(30)),
                      pos_hint={'center_x': 0.5})

        root.add_widget(self._scroll)
        root.add_widget(header)
        root.add_widget(filter_bar)
        root.add_widget(ad)
        root.add_widget(nav)
        self.add_widget(root)

        def _fix(*a):
            header_h = dp(60)
            filter_h = dp(50)
            nav_h = dp(60)
            ad_h = dp(30)
            avail_h = max(dp(120), self.height - header_h - filter_h - nav_h - ad_h)
            self._scroll.pos = (0, nav_h + ad_h)
            self._scroll.height = avail_h
            self._scroll.width = self.width
            self._plant_list_layout.width = self._scroll.width
            filter_bar.pos = (0, self.height - header_h - filter_h)
            filter_bar.height = filter_h
            ad.pos = (self.width / 2 - dp(150), nav_h)
        self._fix_layout = _fix
        Clock.schedule_once(_fix, 0.05)
        self.bind(size=_fix)
        self._render_plants()

    def _build_header(self):
        header = BoxLayout(orientation='horizontal', size_hint=(1, None),
                           height=dp(60), padding=[dp(10), dp(8)], spacing=dp(8))
        with header.canvas.before:
            Color(*COLORS['primary'])
            bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(bg, 'pos', v),
                    size=lambda i, v: setattr(bg, 'size', v))

        back_btn = Button(text='←', font_size=sp(22), size_hint=(None, 1),
                          width=dp(44), background_normal='',
                          background_color=[0, 0, 0, 0], color=COLORS['white'])
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('home', 'right'))

        title_icon = Image(source=icon_path('ic_leaf_white'), size_hint=(None, 1),
                           width=dp(22), allow_stretch=True, keep_ratio=True)

        title = Label(text='لیست گیاهان', font_size=sp(20), bold=True,
                      color=COLORS['white'], halign='right')

        add_btn = Button(text='+', font_size=sp(22), size_hint=(None, 1),
                         width=dp(44), background_normal='',
                         background_color=[0, 0, 0, 0], color=COLORS['white'])
        add_btn.bind(on_press=lambda x: self.app.go_to_screen('add_plant'))

        header.add_widget(back_btn)
        header.add_widget(title_icon)
        header.add_widget(title)
        header.add_widget(add_btn)
        return header

    def _build_filter_bar(self):
        bar = ScrollView(size_hint=(1, None), height=dp(50),
                         do_scroll_y=False, bar_width=0)
        inner = BoxLayout(orientation='horizontal', size_hint=(None, 1),
                          padding=[dp(8), dp(6)], spacing=dp(8))
        inner.bind(minimum_width=inner.setter('width'))
        # چون bar.height از همان لحظه‌ی ساخت مقدار ثابت dp(50) دارد (نه
        # size_hint-محور)، هیچ رویداد تغییری برای .bind(height=...) رخ
        # نمی‌دهد؛ پس این‌جا باید height را یک‌بار مستقیماً همسان کنیم، وگرنه
        # inner (که size_hint_y آن ۱ است) روی ارتفاع پیش‌فرض کیوی می‌ماند.
        inner.height = bar.height

        with bar.canvas.before:
            Color(*COLORS['card'])
            self._filter_bg = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda i, v: setattr(self._filter_bg, 'pos', v),
                 size=lambda i, v: setattr(self._filter_bg, 'size', v))

        filters = ['همه'] + list(set(p['category'] for p in PLANTS_DATA))
        self._filter_btns = {}
        for f in filters:
            is_active = f == self.active_filter
            btn = self._make_filter_btn(f, is_active)
            self._filter_btns[f] = btn
            inner.add_widget(btn)

        self._filter_inner = inner
        bar.add_widget(inner)
        return bar

    def _make_filter_btn(self, label, is_active):
        color = COLORS['primary'] if is_active else COLORS['background']
        text_color = COLORS['white'] if is_active else COLORS['text_secondary']
        btn = Button(
            text=label, font_size=sp(13), bold=is_active,
            size_hint=(None, 1), width=dp(90),
            background_normal='', background_color=[0, 0, 0, 0],
            color=text_color,
        )
        with btn.canvas.before:
            color_instr = Color(*color)
            fbg = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(18)])
        btn.bind(
            pos=lambda i, v, r=fbg: setattr(r, 'pos', v),
            size=lambda i, v, r=fbg: setattr(r, 'size', v),
        )
        # نگه‌داشتن رفرنس به خودِ دستور رنگ، تا بعداً (وقتی کاربر یک تب
        # دیگر را انتخاب می‌کند) بتوانیم بدون ساخت دوباره‌ی دکمه، فقط رنگش
        # را عوض کنیم — پایین را در _apply_filter ببینید.
        btn._bg_color_instr = color_instr
        _lbl = label
        btn.bind(on_press=lambda x, l=_lbl: self._apply_filter(l))
        return btn

    def _apply_filter(self, category):
        self.active_filter = category
        # قبلاً این‌جا فقط لیست گیاهان دوباره رندر می‌شد، ولی خودِ دکمه‌های
        # فیلتر که فقط یک‌بار در _build_filter_bar ساخته شده بودند هیچ‌وقت
        # به‌روزرسانی نمی‌شدند — یعنی فیلتر واقعاً درست کار می‌کرد، ولی
        # کاربر هیچ‌وقت نمی‌دید کدام دسته انتخاب شده. حالا رنگ هر دکمه را
        # مطابق انتخاب تازه به‌روز می‌کنیم، بدون این‌که چیزی از نو ساخته شود.
        for f, btn in getattr(self, '_filter_btns', {}).items():
            is_active = f == self.active_filter
            btn._bg_color_instr.rgba = COLORS['primary'] if is_active else COLORS['background']
            btn.color = COLORS['white'] if is_active else COLORS['text_secondary']
            btn.bold = is_active
        self._render_plants()

    def _render_plants(self):
        if not self._plant_list_layout:
            return
        self._plant_list_layout.clear_widgets()

        all_plants = self.app.all_plants if self.app else PLANTS_DATA

        filtered = []
        for p in all_plants:
            if self.active_filter != 'همه' and p.get('category') != self.active_filter:
                continue
            if self.search_query:
                q = self.search_query.lower()
                if q not in p.get('name', '').lower() and q not in p.get('scientific_name', '').lower():
                    continue
            filtered.append(p)

        count_lbl = Label(
            text=f'{len(filtered)} گیاه یافت شد',
            font_size=sp(12), color=COLORS['text_secondary'],
            size_hint_y=None, height=dp(28), halign='right',
        )
        count_lbl.bind(size=count_lbl.setter('text_size'))
        self._plant_list_layout.add_widget(count_lbl)

        for plant in filtered:
            card = PlantCard(plant_data=plant, app_ref=self.app)
            self._plant_list_layout.add_widget(card)
            self._plant_list_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

        if not filtered:
            empty = Label(text='هیچ گیاهی یافت نشد',
                          font_size=sp(16), color=COLORS['text_secondary'],
                          size_hint_y=None, height=dp(80))
            self._plant_list_layout.add_widget(empty)

    def on_enter(self):
        if getattr(self, '_fix_layout', None):
            self._fix_layout()
        self._render_plants()

