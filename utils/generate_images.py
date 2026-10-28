import os
import struct
import zlib

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'images')
os.makedirs(IMAGES_DIR, exist_ok=True)


CATEGORY_COLORS = {
    'آپارتمانی': (76, 175, 80),
    'گلدار':     (233, 30, 99),
    'دارویی':    (0,  150, 136),
    'درخت میوه':(255, 152,   0),
    'default':   (46, 125,  50),
}

EMOJI_CHAR = {
    'آپارتمانی': 'P',
    'گلدار':     'F',
    'دارویی':    'H',
    'درخت میوه': 'T',
    'default':   'G',
}

def _write_png_chunk(chunk_type, data):
    c = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack('>I', len(data)) + chunk_type + data + struct.pack('>I', c)

def create_png(width, height, r, g, b, label=''):

    sig = b'\x89PNG\r\n\x1a\n'


    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = _write_png_chunk(b'IHDR', ihdr_data)


    raw_rows = []

    tr = min(255, r + 80)
    tg = min(255, g + 80)
    tb = min(255, b + 80)

    for y in range(height):
        row = b'\x00'
        for x in range(width):

            pr = max(0, r - int(20 * y / height))
            pg = max(0, g - int(20 * y / height))
            pb = max(0, b - int(20 * y / height))

            cx, cy = width // 2, height // 2
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            radius = min(width, height) * 0.38
            if dist < radius:

                blend = 1 - dist / radius
                pr2 = int(pr + (tr - pr) * blend * 0.5)
                pg2 = int(pg + (tg - pg) * blend * 0.5)
                pb2 = int(pb + (tb - pb) * blend * 0.5)
                row += bytes([pr2, pg2, pb2])
            else:
                row += bytes([pr, pg, pb])
        raw_rows.append(row)

    raw_data = b''.join(raw_rows)
    compressed = zlib.compress(raw_data, 9)
    idat = _write_png_chunk(b'IDAT', compressed)
    iend = _write_png_chunk(b'IEND', b'')

    return sig + ihdr + idat + iend


PLANT_IMAGES = [
    ('sansevieria.jpg',        'آپارتمانی'),
    ('pothos.jpg',             'آپارتمانی'),
    ('zamioculcas.jpg',        'آپارتمانی'),
    ('ficus_elastica.jpg',     'آپارتمانی'),
    ('monstera.jpg',           'آپارتمانی'),
    ('spathiphyllum.jpg',      'گلدار'),
    ('aglaonema.jpg',          'آپارتمانی'),
    ('dieffenbachia.jpg',      'آپارتمانی'),
    ('dracaena.jpg',           'آپارتمانی'),
    ('chamaedorea.jpg',        'آپارتمانی'),
    ('ficus_benjamina.jpg',    'آپارتمانی'),
    ('cactus.jpg',             'آپارتمانی'),
    ('succulent.jpg',          'آپارتمانی'),
    ('anthurium.jpg',          'گلدار'),
    ('orchid.jpg',             'گلدار'),
    ('african_violet.jpg',     'گلدار'),
    ('begonia.jpg',            'گلدار'),
    ('croton.jpg',             'آپارتمانی'),
    ('philodendron.jpg',       'آپارتمانی'),
    ('areca_palm.jpg',         'آپارتمانی'),
    ('aloe_vera.jpg',          'دارویی'),
    ('haworthia.jpg',          'آپارتمانی'),
    ('kalanchoe.jpg',          'گلدار'),
    ('christmas_cactus.jpg',   'گلدار'),
    ('ivy.jpg',                'آپارتمانی'),
    ('caladium.jpg',           'آپارتمانی'),
    ('peperomia.jpg',          'آپارتمانی'),
    ('ficus_lyrata.jpg',       'آپارتمانی'),
    ('schefflera.jpg',         'آپارتمانی'),
    ('lucky_bamboo.jpg',       'آپارتمانی'),
    ('hoya.jpg',               'آپارتمانی'),
    ('fern.jpg',               'آپارتمانی'),
    ('camellia.jpg',           'گلدار'),
    ('spider_plant.jpg',       'آپارتمانی'),
    ('papyrus.jpg',            'آپارتمانی'),
    ('eucalyptus.jpg',         'آپارتمانی'),
    ('lady_palm.jpg',          'آپارتمانی'),
    ('bromeliad.jpg',          'گلدار'),
    ('tillandsia.jpg',         'آپارتمانی'),
    ('indoor_orange.jpg',      'درخت میوه'),
    ('indoor_lemon.jpg',       'درخت میوه'),
    ('indoor_fig.jpg',         'درخت میوه'),
    ('indoor_banana.jpg',      'درخت میوه'),
    ('indoor_tomato.jpg',      'درخت میوه'),
    ('indoor_pepper.jpg',      'درخت میوه'),
    ('mini_rose.jpg',          'گلدار'),
    ('tuberose.jpg',           'گلدار'),
    ('geranium.jpg',           'گلدار'),
    ('cyclamen.jpg',           'گلدار'),
    ('hyacinth.jpg',           'گلدار'),
    ('narcissus.jpg',          'گلدار'),
    ('gardenia.jpg',           'گلدار'),
    ('bamboo_palm.jpg',        'آپارتمانی'),
    ('syngonium.jpg',          'آپارتمانی'),
    ('maranta.jpg',            'آپارتمانی'),
    ('calathea.jpg',           'آپارتمانی'),
    ('velvet_plant.jpg',       'آپارتمانی'),
    ('rex_begonia.jpg',        'آپارتمانی'),
    ('staghorn_fern.jpg',      'آپارتمانی'),
    ('agave.jpg',              'آپارتمانی'),
    ('hibiscus.jpg',           'گلدار'),
    ('cissus.jpg',             'آپارتمانی'),
    ('tradescantia.jpg',       'آپارتمانی'),
    ('cordyline.jpg',          'آپارتمانی'),
    ('mint.jpg',               'دارویی'),
    ('basil.jpg',              'دارویی'),
    ('rosemary.jpg',           'دارویی'),
    ('thyme.jpg',              'دارویی'),
    ('aloe_ferox.jpg',         'دارویی'),
    ('ornamental_grass.jpg',   'آپارتمانی'),
    ('erica.jpg',              'گلدار'),
    ('celosia.jpg',            'گلدار'),
    ('ivy_geranium.jpg',       'گلدار'),
    ('lavender.jpg',           'دارویی'),
    ('papaya.jpg',             'درخت میوه'),
    ('loquat.jpg',             'درخت میوه'),
    ('pomegranate.jpg',        'درخت میوه'),
    ('rhubarb.jpg',            'درخت میوه'),
    ('strawberry.jpg',         'درخت میوه'),
    ('blueberry.jpg',          'درخت میوه'),

    ('default_plant.png',      'default'),
    ('default_indoor.png',     'آپارتمانی'),
    ('default_flower.png',     'گلدار'),
    ('default_herb.png',       'دارویی'),
    ('default_fruit.png',      'درخت میوه'),
    ('app_icon.png',           'default'),
    ('splash.png',             'default'),
]


def generate_all(force=False):
    total = 0
    skipped = 0
    for filename, category in PLANT_IMAGES:
        path = os.path.join(IMAGES_DIR, filename)
        r, g, b = CATEGORY_COLORS.get(category, CATEGORY_COLORS['default'])


        already_exists = os.path.exists(path) or os.path.exists(
            path.replace('.jpg', '.png') if path.endswith('.jpg') else path
        )
        if already_exists and not force:
            skipped += 1
            continue


        if 'splash' in filename:
            w, h = 480, 800
        elif 'app_icon' in filename:
            w, h = 192, 192
        else:
            w, h = 200, 200

        png_data = create_png(w, h, r, g, b)

        save_path = path if path.endswith('.png') else path.replace('.jpg', '.png')
        with open(save_path, 'wb') as f:
            f.write(png_data)


        if path.endswith('.jpg') and not os.path.exists(path):
            import shutil
            shutil.copy2(save_path, path)

        total += 1
        print(f'  ✓ {filename}')

    if skipped:
        print(f'{skipped} فایل از قبل موجود بود و رد شد (برای بازنویسی، generate_all(force=True) را صدا بزنید)')

    print(f'\n✅ {total} تصویر placeholder ساخته شد در: {IMAGES_DIR}')


if __name__ == '__main__':
    print('🎨 در حال ساخت تصاویر placeholder...')
    generate_all()

