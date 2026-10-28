from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

from components.ui_components import COLORS, PLANT_CATEGORY_COLORS, get_plant_image, icon_path, make_wrapping_label

ICON_MAP = {
    'آپارتمانی': 'ic_leaf',
    'گلدار': 'ic_flower',
    'دارویی': 'ic_herb',
    'درخت میوه': 'ic_fruit',
}


class PlantDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.plant = None

    def load_plant(self, plant_data):
        self.plant = plant_data
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt):
        if not self.plant:
            return
        self.clear_widgets()
        p = self.plant

        root = BoxLayout(orientation='vertical')


        back_row = BoxLayout(size_hint_y=None, height=dp(36), padding=[dp(6), dp(2)])
        with back_row.canvas.before:
            Color(*COLORS['primary'])
            self._back_bg = Rectangle(pos=back_row.pos, size=back_row.size)
        back_row.bind(pos=lambda i, v: setattr(self._back_bg, 'pos', v),
                       size=lambda i, v: setattr(self._back_bg, 'size', v))
        back_btn = Button(
            text='← بازگشت', font_size=sp(14), bold=True,
            color=(1, 1, 1, 1), background_normal='', background_color=(0, 0, 0, 0),
            size_hint=(None, 1), width=dp(90),
        )
        back_btn.bind(on_press=lambda x: self._go_back())
        back_row.add_widget(back_btn)
        back_row.add_widget(Widget())
        root.add_widget(back_row)


        top = BoxLayout(orientation='vertical', size_hint=(1, 1))
        img_path = get_plant_image(p.get('image', ''))

        if img_path:
            photo = Image(
                source=img_path,
                allow_stretch=True,
                size_hint_y=1,
            )
            top.add_widget(photo)
        else:

            cat_color = PLANT_CATEGORY_COLORS.get(p.get('category', ''), COLORS['primary'])
            fallback = FloatLayout(size_hint_y=1)
            with fallback.canvas.before:
                Color(*cat_color[:3], 0.25)
                self._top_bg = Rectangle(pos=fallback.pos, size=fallback.size)
            fallback.bind(pos=lambda i, v: setattr(self._top_bg, 'pos', v),
                          size=lambda i, v: setattr(self._top_bg, 'size', v))
            icon_name = ICON_MAP.get(p.get('category', ''), 'ic_leaf')
            fallback_icon = Image(
                source=icon_path(icon_name),
                allow_stretch=True, keep_ratio=True,
                size_hint=(None, None), size=(dp(110), dp(110)),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
            )
            fallback.add_widget(fallback_icon)
            top.add_widget(fallback)

        root.add_widget(top)


        scroll = ScrollView(size_hint=(1, 1), bar_width=dp(4), do_scroll_x=False)
        info = BoxLayout(orientation='vertical', size_hint_y=None,
                          spacing=dp(15), padding=dp(15))
        info.bind(minimum_height=info.setter('height'))
        scroll.bind(width=info.setter('width'))


        name_lbl = Label(
            text=p.get('name', ''), font_size=sp(20), bold=True,
            color=COLORS['text_dark'], size_hint_y=None, height=dp(32),
            halign='right', valign='middle',
        )
        name_lbl.bind(size=name_lbl.setter('text_size'))
        info.add_widget(name_lbl)

        if p.get('scientific_name'):
            info.add_widget(self._info_label(f"نام علمی: {p['scientific_name']}"))


        rows = [
            ('آبیاری', p.get('watering', '')),
            ('نور', p.get('light', '')),
            ('دما / شرایط رشد', p.get('growth_conditions', '')),
            ('سطح نگهداری', p.get('care_level', '')),
            ('کیفیت هوا', p.get('air', '')),
            ('محدوده قیمت', p.get('price_range', '')),
            ('مناسب برای', p.get('suitable_for', '')),
            ('ویژگی خاص', p.get('special_features', '')),
        ]
        for key, val in rows:
            if val:
                info.add_widget(self._info_label(f'{key}: {val}'))

        self._add_text_block(info, 'توضیحات', p.get('description', ''))
        self._add_text_block(info, 'مشکلات رایج', p.get('common_problems', ''))
        self._add_text_block(info, 'روش درمان', p.get('treatment', ''))

        info.add_widget(Widget(size_hint_y=None, height=dp(20)))

        scroll.add_widget(info)
        root.add_widget(scroll)

        self.add_widget(root)

    def _info_label(self, text):
        return make_wrapping_label(text, font_size=sp(16), color=COLORS['text_dark'],
                                   halign='right', valign='middle')

    def _add_text_block(self, container, title, text):
        if not text:
            return
        title_lbl = Label(
            text=title, font_size=sp(16), bold=True, color=COLORS['primary'],
            size_hint_y=None, height=dp(26), halign='right', valign='middle',
        )
        title_lbl.bind(size=title_lbl.setter('text_size'))
        container.add_widget(title_lbl)

        lbl = make_wrapping_label(text, font_size=sp(16), color=COLORS['text_dark'])
        container.add_widget(lbl)

    def _go_back(self):
        if self.app:
            self.app.go_back()

