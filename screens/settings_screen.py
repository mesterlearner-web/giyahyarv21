from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.clock import Clock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.ui_components import COLORS, AdBanner, SectionTitle, icon_path, ToggleSwitch, is_dark_theme, make_wrapping_label


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
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
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('tools', 'right'))
        header.add_widget(back_btn)
        header.add_widget(Image(source=icon_path('ic_tools_white'), size_hint=(None, 1),
                                 width=dp(24), allow_stretch=True))
        header.add_widget(Label(text='تنظیمات', font_size=sp(20),
                                bold=True, color=COLORS['white'], halign='right'))

        scroll = ScrollView(size_hint=(1, None), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None,
                            spacing=dp(14), padding=[dp(14), dp(14)])
        content.bind(minimum_height=content.setter('height'))
        scroll.bind(width=content.setter('width'))

        content.add_widget(SectionTitle(text='ظاهر برنامه'))
        content.add_widget(self._make_dark_mode_row())

        note = make_wrapping_label(
            'تغییر این گزینه صفحات را دوباره می‌سازد؛ اگر فرمی را در حال '
            'پرکردن بودید، آن را از دست می‌دهید.',
            font_size=sp(11), color=COLORS['text_secondary'],
        )
        content.add_widget(note)

        content.add_widget(SectionTitle(text='درباره'))
        content.add_widget(self._make_about_card())

        content.add_widget(Widget(size_hint_y=None, height=dp(10)))
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
        self.bind(size=_fix)

    def on_enter(self):
        if getattr(self, '_fix_layout', None):
            self._fix_layout()

    def _make_dark_mode_row(self):
        row = BoxLayout(orientation='horizontal', size_hint_y=None,
                        height=dp(78), spacing=dp(12), padding=[dp(14), dp(10)])
        with row.canvas.before:
            Color(*COLORS['card'])
            rbg = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(14)])
        row.bind(pos=lambda i, v: setattr(rbg, 'pos', v),
                 size=lambda i, v: setattr(rbg, 'size', v))

        icon_lbl = Image(source=icon_path('ic_leaf'), size_hint=(None, 1),
                         width=dp(34), color=COLORS['primary'],
                         allow_stretch=True, keep_ratio=True)

        text_col = BoxLayout(orientation='vertical', spacing=dp(3))
        title_lbl = Label(text='حالت تاریک', font_size=sp(15), bold=True,
                          color=COLORS['text_dark'], halign='right', valign='middle',
                          size_hint_y=None, height=dp(24))
        title_lbl.bind(size=title_lbl.setter('text_size'))
        desc_lbl = Label(text='مناسب برای استفاده در محیط کم‌نور', font_size=sp(11.5),
                         color=COLORS['text_secondary'], halign='right', valign='top')
        desc_lbl.bind(size=desc_lbl.setter('text_size'))
        text_col.add_widget(title_lbl)
        text_col.add_widget(desc_lbl)

        switch_holder = FloatLayout(size_hint=(None, 1), width=dp(52))
        switch = ToggleSwitch(active=is_dark_theme(), on_toggle=self._on_theme_toggle,
                              pos_hint={'center_y': 0.5, 'center_x': 0.5})
        switch_holder.add_widget(switch)

        row.add_widget(icon_lbl)
        row.add_widget(text_col)
        row.add_widget(switch_holder)
        return row

    def _on_theme_toggle(self, is_dark):
        if self.app:
            self.app.toggle_theme()

    def _make_about_card(self):
        card = BoxLayout(orientation='vertical', size_hint_y=None,
                         height=dp(90), spacing=dp(4), padding=[dp(14), dp(12)])
        with card.canvas.before:
            Color(*COLORS['card'])
            cbg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(14)])
        card.bind(pos=lambda i, v: setattr(cbg, 'pos', v),
                  size=lambda i, v: setattr(cbg, 'size', v))

        name_lbl = Label(text='گیاهیار', font_size=sp(16), bold=True,
                         color=COLORS['primary'], halign='right', valign='middle',
                         size_hint_y=None, height=dp(26))
        name_lbl.bind(size=name_lbl.setter('text_size'))
        desc_lbl = Label(
            text='دستیار نگهداری از گیاهان خانگی',
            font_size=sp(12), color=COLORS['text_secondary'],
            halign='right', valign='top',
        )
        desc_lbl.bind(size=desc_lbl.setter('text_size'))
        card.add_widget(name_lbl)
        card.add_widget(desc_lbl)
        return card
