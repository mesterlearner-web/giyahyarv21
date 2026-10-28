from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

import webbrowser
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.ui_components import COLORS, AdBanner, SectionTitle, BottomNavBar, icon_path, theme_hex
from data.plants_db import SHOP_CATEGORIES


class ShopScreen(Screen):
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


        header = BoxLayout(orientation='vertical', size_hint=(1, None),
                           height=dp(90), pos_hint={'top': 1})
        with header.canvas.before:
            Color(*theme_hex('#E65100'))
            hbg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(hbg, 'pos', v),
                    size=lambda i, v: setattr(hbg, 'size', v))

        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None,
                            height=dp(60), padding=[dp(10), dp(8)], spacing=dp(8))
        back_btn = Button(text='←', font_size=sp(22), size_hint=(None, 1),
                          width=dp(44), background_normal='',
                          background_color=[0, 0, 0, 0], color=COLORS['white'])
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('home', 'right'))
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Image(source=icon_path('ic_cart_white'), size_hint=(None, 1),
                                 width=dp(22), allow_stretch=True, keep_ratio=True))
        top_bar.add_widget(Label(text='فروشگاه گیاهان', font_size=sp(20),
                                 bold=True, color=COLORS['white'], halign='right'))
        header.add_widget(top_bar)

        sub_lbl = Label(
            text='خرید آنلاین گلدان، گیاه، بذر و کود',
            font_size=sp(12), color=theme_hex('#FFCCBC'),
            size_hint_y=None, height=dp(26), halign='center',
        )
        header.add_widget(sub_lbl)


        scroll = ScrollView(size_hint=(1, None), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None,
                            spacing=dp(14), padding=[dp(14), dp(14)])
        content.bind(minimum_height=content.setter('height'))
        scroll.bind(width=content.setter('width'))

        content.add_widget(SectionTitle(text='دسته‌بندی‌های فروشگاه'))


        grid = GridLayout(cols=2, spacing=dp(12), size_hint_y=None)
        shop_items = [
            {'id': 1, 'icon': 'ic_pot_white', 'title': 'خرید گلدان',
             'desc': 'گلدان‌های سفالی، پلاستیکی، آویزی و دکوری',
             'url': 'https://www.digikala.com/search/?q=گلدان',
             'color': theme_hex('#5D4037'),
             'bg': theme_hex('#EFEBE9')},
            {'id': 2, 'icon': 'ic_flower_white', 'title': 'خرید گل و گیاه',
             'desc': 'گیاهان آپارتمانی، گل‌دار و مصنوعی',
             'url': 'https://www.digikala.com/search/?q=گیاه+آپارتمانی',
             'color': theme_hex('#880E4F'),
             'bg': theme_hex('#FCE4EC')},
            {'id': 3, 'icon': 'ic_herb_white', 'title': 'خرید بذر',
             'desc': 'بذر سبزیجات، گل‌ها و گیاهان دارویی',
             'url': 'https://www.digikala.com/search/?q=بذر+گیاه',
             'color': theme_hex('#1B5E20'),
             'bg': theme_hex('#E8F5E9')},
            {'id': 4, 'icon': 'ic_leaf_white', 'title': 'خرید کود',
             'desc': 'کود آلی، شیمیایی، مایع و گرانول',
             'url': 'https://www.digikala.com/search/?q=کود+گیاه',
             'color': theme_hex('#33691E'),
             'bg': theme_hex('#F1F8E9')},
        ]
        total_h = 0
        for item in shop_items:
            card = self._make_shop_card(item)
            grid.add_widget(card)

        rows = (len(shop_items) + 1) // 2
        grid.height = rows * dp(140) + (rows - 1) * dp(12)
        content.add_widget(grid)


        content.add_widget(SectionTitle(text='پیشنهادات ویژه'))
        special_items = [
            {'icon': 'ic_medical_white', 'title': 'سموم و آفت‌کش‌ها',
             'desc': 'انواع سموم مجاز برای کنترل آفات گیاهی',
             'url': 'https://www.digikala.com/search/?q=سم+آفت+کش+گیاه',
             'color': theme_hex('#B71C1C')},
            {'icon': 'ic_droplet_white', 'title': 'ابزار آبیاری',
             'desc': 'آبپاش، سیستم قطره‌ای، شیلنگ و...',
             'url': 'https://www.digikala.com/search/?q=ابزار+آبیاری+گیاه',
             'color': theme_hex('#01579B')},
            {'icon': 'ic_pot_white', 'title': 'خاک و بستر کشت',
             'desc': 'خاک مخصوص آپارتمانی، پرلیت، پیت',
             'url': 'https://www.digikala.com/search/?q=خاک+کشت+گیاه',
             'color': theme_hex('#4E342E')},
            {'icon': 'ic_tools_white', 'title': 'ابزار باغبانی',
             'desc': 'قیچی هرس، بیل، کنجکاو، دستکش',
             'url': 'https://www.digikala.com/search/?q=ابزار+باغبانی',
             'color': theme_hex('#37474F')},
        ]
        for item in special_items:
            card = self._make_list_card(item)
            content.add_widget(card)


        content.add_widget(SectionTitle(text='راهنمای خرید'))
        tips_card = BoxLayout(orientation='vertical', size_hint_y=None,
                              height=dp(140), padding=dp(14))
        with tips_card.canvas.before:
            Color(*theme_hex('#FFF8E1'))
            tbbg = RoundedRectangle(pos=tips_card.pos, size=tips_card.size, radius=[dp(12)])
        tips_card.bind(pos=lambda i, v: setattr(tbbg, 'pos', v),
                       size=lambda i, v: setattr(tbbg, 'size', v))

        tips_text = [
            'برای خرید هر دسته روی آن کلیک کنید',
            'در سایت می‌توانید قیمت‌ها را مقایسه کنید',
            'ارسال سریع به سراسر ایران',
            'فقط محصولات معتبر و با کیفیت',
        ]
        for tip in tips_text:
            tips_card.add_widget(Label(text=tip, font_size=sp(12),
                                       color=COLORS['text_dark'],
                                       size_hint_y=None, height=dp(28),
                                       halign='right'))
        content.add_widget(tips_card)
        content.add_widget(Widget(size_hint_y=None, height=dp(10)))

        scroll.add_widget(content)

        nav = BottomNavBar(app_ref=self.app, active_tab='shop')
        nav.pos_hint = {'x': 0, 'y': 0}
        ad = AdBanner(size_hint=(None, None), size=(dp(300), dp(30)),
                      pos_hint={'center_x': 0.5})

        root.add_widget(scroll)
        root.add_widget(header)
        root.add_widget(ad)
        root.add_widget(nav)
        self.add_widget(root)

        def _fix(*a):
            avail_h = max(dp(120), self.height - dp(90) - dp(60) - dp(30))
            scroll.pos = (0, dp(60) + dp(30))
            scroll.height = avail_h
            scroll.width = self.width
            content.width = scroll.width
            ad.pos = (self.width / 2 - dp(150), dp(60))
        self._fix_layout = _fix
        Clock.schedule_once(_fix, 0.05)
        self.bind(size=_fix)

    def on_enter(self):
        if getattr(self, '_fix_layout', None):
            self._fix_layout()

    def _make_shop_card(self, item):
        card = Button(background_normal='', background_color=[0, 0, 0, 0],
                      size_hint_y=None, height=dp(140))
        with card.canvas.before:
            Color(*item['bg'])
            cbg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(14)])
        card.bind(pos=lambda i, v: setattr(cbg, 'pos', v),
                  size=lambda i, v: setattr(cbg, 'size', v))

        inner = BoxLayout(orientation='vertical', spacing=dp(6),
                          padding=[dp(12), dp(10)],
                          pos=card.pos, size=card.size)
        card.bind(pos=lambda i, v: setattr(inner, 'pos', v),
                  size=lambda i, v: setattr(inner, 'size', v))

        icon_row = BoxLayout(size_hint_y=None, height=dp(48))
        icon_row.add_widget(Widget())
        icon_row.add_widget(Image(source=icon_path(item['icon']), size_hint=(None, 1),
                                  width=dp(40), color=item['color'],
                                  allow_stretch=True, keep_ratio=True))
        icon_row.add_widget(Widget())
        inner.add_widget(icon_row)
        inner.add_widget(Label(text=item['title'], font_size=sp(14), bold=True,
                               color=item['color'], size_hint_y=None, height=dp(24),
                               halign='center'))
        inner.add_widget(Label(text=item['desc'], font_size=sp(10),
                               color=COLORS['text_secondary'],
                               halign='center'))
        card.add_widget(inner)

        _url = item['url']
        card.bind(on_press=lambda x, u=_url: self._open_url(u))
        return card

    def _make_list_card(self, item):
        card = Button(background_normal='', background_color=[0, 0, 0, 0],
                      size_hint_y=None, height=dp(72))
        with card.canvas.before:
            Color(*COLORS['card'])
            cbg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda i, v: setattr(cbg, 'pos', v),
                  size=lambda i, v: setattr(cbg, 'size', v))

        inner = BoxLayout(orientation='horizontal', spacing=dp(14),
                          padding=[dp(14), dp(10)],
                          pos=card.pos, size=card.size)
        card.bind(pos=lambda i, v: setattr(inner, 'pos', v),
                  size=lambda i, v: setattr(inner, 'size', v))

        inner.add_widget(Image(source=icon_path(item['icon']), size_hint=(None, 1),
                               width=dp(40), color=item['color'],
                               allow_stretch=True, keep_ratio=True))

        text_col = BoxLayout(orientation='vertical', spacing=dp(2))
        text_col.add_widget(Label(text=item['title'], font_size=sp(15), bold=True,
                                   color=item['color'], halign='right',
                                   size_hint_y=None, height=dp(26)))
        desc = Label(text=item['desc'], font_size=sp(11),
                     color=COLORS['text_secondary'], halign='right')
        desc.bind(size=desc.setter('text_size'))
        text_col.add_widget(desc)
        inner.add_widget(text_col)

        inner.add_widget(Label(text='›', font_size=sp(24), color=item['color'],
                               size_hint=(None, 1), width=dp(20)))
        card.add_widget(inner)

        _url = item['url']
        card.bind(on_press=lambda x, u=_url: self._open_url(u))
        return card

    def _open_url(self, url):
        try:
            from kivy.utils import platform
            if platform == 'android':
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                activity = cast('android.app.Activity', PythonActivity.mActivity)
                activity.startActivity(intent)
            else:
                import webbrowser
                webbrowser.open(url)
        except Exception as e:
            print(f'خطا در باز کردن مرورگر: {e}')

