from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse
from kivy.utils import get_color_from_hex
from kivy.clock import Clock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.ui_components import COLORS, AdBanner, SectionTitle, BottomNavBar, icon_path, theme_hex
from utils.helpers import rtl


class ToolsScreen(Screen):
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
        back_btn.bind(on_press=lambda x: self.app.go_to_screen('home', 'right'))
        header.add_widget(back_btn)
        header.add_widget(Image(source=icon_path('ic_tools_white'), size_hint=(None, 1),
                                 width=dp(24), allow_stretch=True))
        header.add_widget(Label(text='ابزار مراقبت', font_size=sp(20),
                                bold=True, color=COLORS['white'], halign='right'))


        scroll = ScrollView(size_hint=(1, None), do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None,
                            spacing=dp(14), padding=[dp(14), dp(14)])
        content.bind(minimum_height=content.setter('height'))
        # نکته‌ی مهم: ScrollView خودش size_hint_x فرزندش را به‌طور خودکار به
        # پیکسل واقعی تبدیل نمی‌کند (برخلاف BoxLayout/FloatLayout که این کار
        # را برای فرزندانشان انجام می‌دهند) — چون ScrollView خودش یک Layout
        # به آن معنا نیست. بدون این خط، 'content' روی عرض پیش‌فرض و کوچک
        # کیوی می‌ماند و کل لیست کارت‌ها عملاً نامرئی/بیرون از دید می‌شود.
        scroll.bind(width=content.setter('width'))

        content.add_widget(SectionTitle(text='ابزارهای در دسترس'))

        tools = [
            {
                'icon': 'ic_clock_white',
                'title': 'یادآور آبیاری و کوددهی',
                'desc': 'تنظیم تایمر شمارش معکوس برای آبیاری، کوددهی و سایر مراقبت‌های دوره‌ای',
                'screen': 'timers',
                'color': theme_hex('#1565C0'),
                'bg': theme_hex('#E3F2FD'),
            },
            {
                'icon': 'ic_bot_white',
                'title': 'دستیار هوشمند',
                'desc': 'تحلیل عکس گیاه با هوش مصنوعی DeepSeek Vision و تشخیص مشکل',
                'screen': 'ai_vet',
                'ai_vet_mode': 'vision',
                'color': theme_hex('#00838F'),
                'bg': theme_hex('#E0F7FA'),
            },
            {
                'icon': 'ic_medical_white',
                'title': 'مشاوره گیاه‌پزشکی',
                'desc': 'با تایپ سوال یا ارسال عکس، با هوش مصنوعی چت کنید',
                'screen': 'ai_vet',
                'ai_vet_mode': 'chat',
                'color': theme_hex('#2E7D32'),
                'bg': theme_hex('#E8F5E9'),
            },
            {
                'icon': 'ic_clipboard_white',
                'title': 'لیست گیاهان',
                'desc': 'مشاهده اطلاعات کامل تمام گیاهان',
                'screen': 'plant_list',
                'color': theme_hex('#6A1B9A'),
                'bg': theme_hex('#F3E5F5'),
            },
            {
                'icon': 'ic_plus_white',
                'title': 'افزودن گیاه جدید',
                'desc': 'گیاهان سفارشی خود را اضافه کنید',
                'screen': 'add_plant',
                'color': theme_hex('#E65100'),
                'bg': theme_hex('#FFF3E0'),
            },
            {
                'icon': 'ic_tools_white',
                'title': 'تنظیمات',
                'desc': 'حالت تاریک و سایر تنظیمات برنامه',
                'screen': 'settings',
                'color': theme_hex('#37474F'),
                'bg': theme_hex('#F5F5F5'),
            },
        ]

        for t in tools:
            card = self._make_tool_card(t)
            content.add_widget(card)


        content.add_widget(SectionTitle(text='راهنمای سریع'))
        tips = [
            ('ic_droplet', 'آبیاری منظم', 'اکثر گیاهان آپارتمانی به آبیاری هر ۷-۱۰ روز یکبار نیاز دارند.'),
            ('ic_sun', 'نور مناسب', 'گیاهان را از نور مستقیم تابستان دور نگه دارید.'),
            ('ic_medical', 'دما', 'دمای ایده‌آل برای اکثر گیاهان ۱۸ تا ۲۸ درجه است.'),
            ('ic_droplet', 'رطوبت', 'گیاهان استوایی به رطوبت بالاتری نیاز دارند.'),
            ('ic_herb', 'خاک', 'هر ۲-۳ سال یکبار خاک و گلدان را عوض کنید.'),
        ]
        for icon, title, tip in tips:
            tip_card = self._make_tip_card(icon, title, tip)
            content.add_widget(tip_card)

        content.add_widget(Widget(size_hint_y=None, height=dp(10)))
        scroll.add_widget(content)


        nav = BottomNavBar(app_ref=self.app, active_tab='tools')
        nav.pos_hint = {'x': 0, 'y': 0}
        ad = AdBanner(size_hint=(None, None), size=(dp(300), dp(30)),
                      pos_hint={'center_x': 0.5})

        root.add_widget(scroll)
        root.add_widget(header)
        root.add_widget(ad)
        root.add_widget(nav)
        self.add_widget(root)

        def _fix(*a):
            avail_h = max(dp(120), self.height - dp(60) - dp(60) - dp(30))
            scroll.pos = (0, dp(60) + dp(30))
            scroll.height = avail_h
            scroll.width = self.width
            content.width = scroll.width
            ad.pos = (self.width / 2 - dp(150), dp(60))
        self._fix_layout = _fix
        Clock.schedule_once(_fix, 0.05)
        # چرا فقط یک‌بار کافی نیست: وقتی این صفحه ساخته می‌شود، اگر هنوز
        # صفحه‌ی *فعال* (current) در ScreenManager نباشد، self.width/height
        # ممکن است هنوز اندازه‌ی نهایی/واقعی خود را نگرفته باشند؛ چون
        # scroll با size_hint_y=None ساخته شده (ارتفاعش را خودمان دستی
        # می‌دهیم، نه فرزندِ خودکارِ FloatLayout)، اگر همان یک اجرای اولیه
        # با self.height اشتباه/موقت محاسبه شود، هیچ‌وقت خودش را دوباره
        # تصحیح نمی‌کند و صفحه برای همیشه خالی/نامرئی می‌ماند — دقیقاً همان
        # چیزی که در تست روی گوشی دیده شد. bind زیر باعث می‌شود هر بار اندازه‌ی
        # واقعیِ صفحه مشخص/عوض شد، _fix دوباره با مقادیر درست اجرا شود؛
        # on_enter هم یک تضمین اضافه است چون دقیقاً لحظه‌ای که صفحه واقعاً
        # روی صفحه‌نمایش می‌آید، self.size قطعاً درست است.
        self.bind(size=_fix)

    def on_enter(self):
        if getattr(self, '_fix_layout', None):
            self._fix_layout()

    def _make_tool_card(self, tool_data):
        disabled = tool_data.get('disabled', False)

        card = Button(
            background_normal='', background_color=[0, 0, 0, 0],
            size_hint_y=None, height=dp(90),
        )
        with card.canvas.before:
            Color(*tool_data['bg'])
            cbg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(14)])
        card.bind(pos=lambda i, v: setattr(cbg, 'pos', v),
                  size=lambda i, v: setattr(cbg, 'size', v))

        inner = BoxLayout(orientation='horizontal', spacing=dp(14),
                          padding=[dp(14), dp(10)],
                          pos=card.pos, size=card.size)
        card.bind(pos=lambda i, v: setattr(inner, 'pos', v),
                  size=lambda i, v: setattr(inner, 'size', v))

        icon_lbl = Image(source=icon_path(tool_data['icon']), size_hint=(None, 1),
                         width=dp(55), color=tool_data['color'],
                         allow_stretch=True, keep_ratio=True)

        text_col = BoxLayout(orientation='vertical', spacing=dp(4))
        title_lbl = Label(text=tool_data['title'], font_size=sp(16), bold=True,
                          color=tool_data['color'], halign='right', valign='middle',
                          size_hint_y=None, height=dp(30))
        title_lbl.bind(size=title_lbl.setter('text_size'))

        desc_lbl = Label(text=tool_data['desc'], font_size=sp(12),
                         color=COLORS['text_secondary'], halign='right',
                         valign='top')
        desc_lbl.bind(size=desc_lbl.setter('text_size'))

        text_col.add_widget(title_lbl)
        text_col.add_widget(desc_lbl)

        inner.add_widget(icon_lbl)
        inner.add_widget(text_col)

        if disabled:
            badge = Label(
                text=tool_data.get('badge', 'در دسترس نیست'),
                font_size=sp(10.5), bold=True,
                color=theme_hex('#757575'),
                size_hint=(None, 1), width=dp(80),
                halign='center', valign='middle',
            )
            badge.bind(size=badge.setter('text_size'))
            with badge.canvas.before:
                Color(*theme_hex('#E0E0E0'))
                bbg = RoundedRectangle(pos=badge.pos, size=(dp(72), dp(24)), radius=[dp(12)])
            def _sync_badge_bg(inst, val, r=bbg):
                r.pos = (inst.center_x - dp(36), inst.center_y - dp(12))
            badge.bind(pos=_sync_badge_bg, size=_sync_badge_bg)
            inner.add_widget(badge)
        else:
            arrow = Label(text='›', font_size=sp(26), color=tool_data['color'],
                          size_hint=(None, 1), width=dp(20))
            inner.add_widget(arrow)

        card.add_widget(inner)

        if disabled:
            _title = tool_data['title']
            card.bind(on_press=lambda x, t=_title: self._show_unavailable_message(t))
        else:
            _scr = tool_data['screen']
            _mode = tool_data.get('ai_vet_mode')
            card.bind(on_press=lambda x, s=_scr, m=_mode: self._navigate_tool(s, m))
        return card

    def _navigate_tool(self, screen_name, ai_vet_mode=None):
        # صفحه‌ی دستیار هوشمند دو تب دارد (چت / تحلیل تصویر)؛ این‌جا تعیین
        # می‌کنیم با ورود، کدام تب باز شود (AIVetScreen.on_enter آن را
        # می‌خواند). برای بقیه‌ی صفحات، ai_vet_mode همیشه None است و بدون
        # اثر رد می‌شود.
        if ai_vet_mode and self.app:
            self.app.pending_ai_vet_mode = ai_vet_mode
        if self.app:
            self.app.go_to_screen(screen_name)

    def _show_unavailable_message(self, title):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        with content.canvas.before:
            Color(*COLORS['card'])
            _uc_bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(pos=lambda i, v: setattr(_uc_bg, 'pos', v),
                    size=lambda i, v: setattr(_uc_bg, 'size', v))
        content.add_widget(Label(
            text=f'«{title}» هنوز در دسترس نیست و به‌زودی اضافه می‌شود.',
            font_size=sp(14), color=COLORS['text_dark'], halign='center', valign='middle',
        ))
        ok_btn = Button(text='باشه', size_hint_y=None, height=dp(44),
                        background_normal='', background_color=COLORS['primary'],
                        color=COLORS['white'])
        content.add_widget(ok_btn)
        popup = Popup(title=rtl('در دسترس نیست'), content=content,
                      size_hint=(0.8, 0.32), auto_dismiss=True)
        ok_btn.bind(on_press=lambda x: popup.dismiss())
        popup.open()

    def _make_tip_card(self, icon, title, tip):
        outer = BoxLayout(orientation='horizontal', size_hint_y=None,
                          height=dp(70), spacing=dp(12), padding=[dp(12), dp(8)])
        with outer.canvas.before:
            Color(*COLORS['card'])
            bg = RoundedRectangle(pos=outer.pos, size=outer.size, radius=[dp(10)])
        outer.bind(pos=lambda i, v: setattr(bg, 'pos', v),
                   size=lambda i, v: setattr(bg, 'size', v))

        outer.add_widget(Image(source=icon_path(icon), size_hint=(None, 1),
                               width=dp(40), color=COLORS['primary'],
                               allow_stretch=True, keep_ratio=True))
        inner = BoxLayout(orientation='vertical', spacing=dp(2))
        inner.add_widget(Label(text=title, font_size=sp(13), bold=True,
                               color=COLORS['text_primary'], halign='right',
                               size_hint_y=None, height=dp(24)))
        desc = Label(text=tip, font_size=sp(11), color=COLORS['text_secondary'],
                     halign='right', valign='top')
        desc.bind(size=desc.setter('text_size'))
        inner.add_widget(desc)
        outer.add_widget(inner)
        return outer



