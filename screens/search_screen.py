from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.ui_components import COLORS, AdBanner, PlantCard, icon_path, PersianTextInput, theme_hex
from data.plants_db import PLANTS_DATA, search_plants


class SearchScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self._results_layout = None
        self._search_input = None
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt):
        root = FloatLayout()
        with root.canvas.before:
            Color(*COLORS['background'])
            bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(bg, 'pos', v),
                  size=lambda i, v: setattr(bg, 'size', v))


        header = BoxLayout(orientation='vertical', size_hint=(1, None),
                           height=dp(110), pos_hint={'top': 1})
        with header.canvas.before:
            Color(*COLORS['primary'])
            hbg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(hbg, 'pos', v),
                    size=lambda i, v: setattr(hbg, 'size', v))

        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(56), padding=[dp(10), dp(8)], spacing=dp(8))
        back_btn = Button(text='←', font_size=sp(22), size_hint=(None, 1),
                          width=dp(44), background_normal='',
                          background_color=[0, 0, 0, 0], color=COLORS['white'])
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('home', 'right'))
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Image(source=icon_path('ic_search_white'), size_hint=(None, 1),
                                 width=dp(22), allow_stretch=True, keep_ratio=True))
        top_bar.add_widget(Label(text='جستجوی گیاهان', font_size=sp(19),
                                 bold=True, color=COLORS['white'], halign='right'))


        search_box = BoxLayout(orientation='horizontal', size_hint_y=None,
                               height=dp(44), padding=[dp(10), dp(4)], spacing=dp(8))
        self._search_input = PersianTextInput(
            hint_text='نام گیاه، نام علمی یا دسته...',
            font_size=sp(14), multiline=False,
            background_color=COLORS['white'],
            foreground_color=COLORS['text_dark'],
            hint_text_color=theme_hex('#A5D6A7'),
            halign='right',
        )
        self._search_input.bind(raw_text=self._on_search_text)

        srch_btn = Button(text='', font_size=sp(18), size_hint=(None, 1),
                          width=dp(44), background_normal='',
                          background_color=theme_hex('#1B5E20'),
                          color=COLORS['white'])
        srch_btn_icon = Image(source=icon_path('ic_search_white'), size_hint=(1, 1),
                              allow_stretch=True, keep_ratio=True)
        srch_btn.add_widget(srch_btn_icon)
        srch_btn.bind(pos=lambda i, v: setattr(srch_btn_icon, 'pos', v),
                      size=lambda i, v: setattr(srch_btn_icon, 'size', v))
        srch_btn.bind(on_press=lambda x: self._do_search(self._search_input.raw_text))

        search_box.add_widget(srch_btn)
        search_box.add_widget(self._search_input)

        header.add_widget(top_bar)
        header.add_widget(search_box)


        scroll = ScrollView(size_hint=(1, None), do_scroll_x=False)
        self._results_layout = BoxLayout(orientation='vertical', size_hint_y=None,
                                         spacing=dp(6), padding=[dp(12), dp(10)])
        self._results_layout.bind(minimum_height=self._results_layout.setter('height'))
        scroll.add_widget(self._results_layout)
        self._scroll = scroll
        scroll.bind(width=self._results_layout.setter('width'))

        ad = AdBanner(size_hint=(None, None), size=(dp(300), dp(30)),
                      pos_hint={'center_x': 0.5})

        root.add_widget(scroll)
        root.add_widget(header)
        root.add_widget(ad)
        self.add_widget(root)

        def _fix(*a):
            avail_h = max(dp(120), self.height - dp(110) - dp(30))
            scroll.pos = (0, dp(30))
            scroll.height = avail_h
            scroll.width = self.width
            self._results_layout.width = scroll.width
            ad.pos = (self.width / 2 - dp(150), 0)
        self._fix_layout = _fix
        Clock.schedule_once(_fix, 0.05)
        self.bind(size=_fix)
        self._show_initial()

    def _show_initial(self):
        if not self._results_layout:
            return
        self._results_layout.clear_widgets()


        suggestions = [
            ('مقاوم‌ترین‌ها', 'بسیار آسان'),
            ('گل‌دار', 'گلدار'),
            ('دارویی', 'دارویی'),
            ('درخت میوه', 'درخت میوه'),
            ('نخل', 'نخل'),
            ('فیکوس', 'فیکوس'),
        ]
        sug_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80),
                            spacing=dp(6), padding=[dp(0), dp(6)])
        sug_box.add_widget(Label(text='جستجوهای پیشنهادی:', font_size=sp(12),
                                  color=COLORS['text_secondary'],
                                  size_hint_y=None, height=dp(20), halign='right'))
        tags_row = BoxLayout(orientation='horizontal', size_hint_y=None,
                             height=dp(34), spacing=dp(8))
        for label, query in suggestions:
            btn = Button(text=label, font_size=sp(11), size_hint=(None, 1),
                         width=dp(85), background_normal='',
                         background_color=theme_hex('#E8F5E9'),
                         color=COLORS['primary'])
            with btn.canvas.before:
                Color(*COLORS['divider'])
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
            _q = query
            btn.bind(on_press=lambda x, q=_q: self._do_search(q))
            tags_row.add_widget(btn)
        sug_box.add_widget(tags_row)
        self._results_layout.add_widget(sug_box)


        plants_to_show = self.app.all_plants[:10] if self.app else PLANTS_DATA[:10]
        count_lbl = Label(text='۱۰ گیاه اخیر', font_size=sp(12),
                          color=COLORS['text_secondary'],
                          size_hint_y=None, height=dp(28), halign='right')
        count_lbl.bind(size=count_lbl.setter('text_size'))
        self._results_layout.add_widget(count_lbl)

        for p in plants_to_show:
            card = PlantCard(plant_data=p, app_ref=self.app)
            self._results_layout.add_widget(card)
            self._results_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

    def _on_search_text(self, instance, value):
        Clock.unschedule(self._delayed_search)
        if len(value) >= 2:
            Clock.schedule_once(self._delayed_search, 0.4)
        elif not value:
            self._show_initial()

    def _delayed_search(self, dt):
        if self._search_input:
            self._do_search(self._search_input.raw_text)

    def _do_search(self, query):
        if not self._results_layout:
            return
        query = query.strip()
        if not query:
            self._show_initial()
            return

        if self._search_input:
            self._search_input.raw_text = query

        all_plants = self.app.all_plants if self.app else PLANTS_DATA
        results = []
        q = query.lower()
        for p in all_plants:
            if (q in p.get('name', '').lower() or
                    q in p.get('scientific_name', '').lower() or
                    q in p.get('category', '').lower() or
                    q in p.get('description', '').lower() or
                    q in p.get('special_features', '').lower() or
                    q in p.get('care_level', '').lower()):
                results.append(p)

        self._results_layout.clear_widgets()
        count_lbl = Label(
            text=f'نتایج جستجو برای «{query}»: {len(results)} مورد',
            font_size=sp(12), color=COLORS['text_secondary'],
            size_hint_y=None, height=dp(32), halign='right',
        )
        count_lbl.bind(size=count_lbl.setter('text_size'))
        self._results_layout.add_widget(count_lbl)

        if results:
            for p in results:
                card = PlantCard(plant_data=p, app_ref=self.app)
                self._results_layout.add_widget(card)
                self._results_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))
        else:
            empty = BoxLayout(orientation='vertical', size_hint_y=None,
                              height=dp(160), padding=dp(20))
            empty.add_widget(Image(source=icon_path('ic_search'), size_hint_y=None,
                                    height=dp(60), allow_stretch=True, keep_ratio=True))
            empty.add_widget(Label(
                text=f'گیاهی با نام «{query}» یافت نشد.\nسعی کنید با کلمات دیگری جستجو کنید.',
                font_size=sp(14), color=COLORS['text_secondary'],
                halign='center',
            ))
            self._results_layout.add_widget(empty)

    def on_enter(self):
        if getattr(self, '_fix_layout', None):
            self._fix_layout()
        if self._search_input:
            self._search_input.raw_text = ''
        self._show_initial()

