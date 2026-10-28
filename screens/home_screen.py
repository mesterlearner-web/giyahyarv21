from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

from components.ui_components import COLORS, PlantImage, BottomNavBar, get_plant_image, icon_path
from data.plants_db import PLANTS_DATA


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt):
        root = BoxLayout(orientation='vertical')

        with root.canvas.before:
            Color(*COLORS['background'])
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(self._bg, 'pos', v),
                  size=lambda i, v: setattr(self._bg, 'size', v))


        header = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(16), dp(10)], spacing=dp(8))
        with header.canvas.before:
            Color(*COLORS['primary'])
            self._hdr_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: setattr(self._hdr_bg, 'pos', v),
                    size=lambda i, v: setattr(self._hdr_bg, 'size', v))
        header.add_widget(Image(source=icon_path('ic_leaf_white'), size_hint=(None, 1),
                                 width=dp(28), allow_stretch=True))
        header.add_widget(Label(text='گیاهیار', font_size=sp(20), bold=True,
                                 color=COLORS['white']))
        root.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1), bar_width=dp(4), do_scroll_x=False)
        grid = GridLayout(
            cols=3,
            spacing=dp(10),
            padding=dp(10),
            size_hint_y=None,
        )
        grid.bind(minimum_height=grid.setter('height'))
        # ScrollView خودش size_hint_x فرزندش را به پیکسل واقعی تبدیل نمی‌کند؛
        # این خط عرض گرید را صریحاً با عرض scroll هماهنگ نگه می‌دارد.
        scroll.bind(width=grid.setter('width'))

        plants = self.app.all_plants if self.app else list(PLANTS_DATA)
        for plant in plants:
            grid.add_widget(self._make_grid_item(plant))

        scroll.add_widget(grid)
        root.add_widget(scroll)


        nav = BottomNavBar(app_ref=self.app, active_tab='home')
        root.add_widget(nav)

        self.add_widget(root)

    def _make_grid_item(self, plant):
        btn = Button(
            background_normal='',
            background_color=(0, 0, 0, 0),
            size_hint_y=None,
            size_hint_x=1,
            height=dp(120),
        )

        inner = BoxLayout(orientation='vertical', spacing=dp(2),
                           pos=btn.pos, size=btn.size)
        btn.bind(pos=lambda i, v: setattr(inner, 'pos', v),
                 size=lambda i, v: setattr(inner, 'size', v))


        img = PlantImage(
            plant_name=plant.get('name', ''),
            category=plant.get('category', 'آپارتمانی'),
            image_path=get_plant_image(plant.get('image', '')),
            size_hint=(1, 0.7),
        )
        inner.add_widget(img)


        name_lbl = Label(
            text=plant.get('name', ''),
            font_size=sp(13),
            color=COLORS['text_dark'],
            halign='center',
            valign='top',
            size_hint=(1, 0.3),
            shorten=True,
            shorten_from='right',
        )
        name_lbl.bind(size=lambda i, v: setattr(name_lbl, 'text_size', v))
        inner.add_widget(name_lbl)

        btn.add_widget(inner)

        plant_id = plant.get('id')
        btn.bind(on_press=lambda x, pid=plant_id: self._open_plant(pid))
        return btn

    def _open_plant(self, plant_id):
        if self.app:
            self.app.show_plant_detail(plant_id)

    def on_enter(self):
        pass

