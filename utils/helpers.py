from datetime import datetime, timedelta


try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _RESHAPE_AVAILABLE = True
except ImportError:
    _RESHAPE_AVAILABLE = False


def rtl(text):
    if not text or not isinstance(text, str) or not _RESHAPE_AVAILABLE:
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def wrap_rtl_text(text, font_name='Roboto', font_size=16, max_width=300, bold=False):
    """متنِ فارسیِ بلند و چندخطی را برای نمایش در یک Label راست‌چین آماده
    می‌کند: به‌جای این‌که کل متن یک‌جا rtl() شود و بعد خودِ Kivy آن را بر
    اساس عرض بشکند (که چون شکستن روی رشته‌ی از قبل بازچینی‌شده اتفاق
    می‌افتد، ترتیب خط‌ها و بعضی کلمه‌ها سرِ خط درهم/ناقص می‌شوند)، ابتدا با
    اندازه‌گیریِ واقعیِ عرضِ هر کلمه از خودِ موتور فونت کیوی، نقطه‌ی شکستِ
    هر خط را روی متنِ اصلی (قبل از rtl) پیدا می‌کند، و فقط بعد از آن هر
    خط را جدا و مستقل rtl() می‌کند. اگر اندازه‌گیریِ کیوی به هر دلیلی در
    دسترس نبود، به همان رفتار قبلی (rtl روی کل متن) برمی‌گردد — یعنی
    بدترین حالت، نه بهتر نه بدتر از قبل.
    """
    if not text or not isinstance(text, str):
        return text
    try:
        from kivy.core.text import Label as _CoreLabel
        measurer = _CoreLabel(font_name=font_name, font_size=font_size, bold=bold)

        out_lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split(' ')
            current = ''
            for word in words:
                candidate = f'{current} {word}'.strip() if current else word
                w, h = measurer.get_extents(candidate)
                if w <= max_width or not current:
                    current = candidate
                else:
                    out_lines.append(current)
                    current = word
            out_lines.append(current)

        return '\n'.join(rtl(ln) if ln else '' for ln in out_lines)
    except Exception:
        return rtl(text)


_FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

def to_persian_num(n):
    return str(n).translate(_FA_DIGITS)


WEEKDAYS_FA = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه', 'شنبه', 'یکشنبه']
MONTHS_FA   = ['', 'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
               'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']

def format_date_fa(dt: datetime) -> str:
    weekday = WEEKDAYS_FA[dt.weekday()]
    return f"{weekday} {to_persian_num(dt.day)} / {to_persian_num(dt.month)} / {to_persian_num(dt.year)}"


def days_until(iso_str: str) -> int:
    try:
        target = datetime.fromisoformat(iso_str)
        delta = (target - datetime.now()).days
        return delta
    except Exception:
        return 0


def relative_time_fa(iso_str: str) -> str:
    days = days_until(iso_str)
    if days < 0:
        return f'{to_persian_num(abs(days))} روز گذشته'
    if days == 0:
        return 'امروز!'
    if days == 1:
        return 'فردا'
    return f'{to_persian_num(days)} روز دیگر'


def next_due_date(interval_days: int) -> str:
    return (datetime.now() + timedelta(days=interval_days)).isoformat()


def is_overdue(iso_str: str) -> bool:
    try:
        return datetime.fromisoformat(iso_str) < datetime.now()
    except Exception:
        return False


CARE_COLOR = {
    'بسیار آسان': '#43A047',
    'آسان':        '#66BB6A',
    'متوسط':       '#FFA726',
    'سخت':         '#EF5350',
}

def care_color(level: str) -> str:
    for k, v in CARE_COLOR.items():
        if k in level:
            return v
    return '#757575'


def validate_plant_form(data: dict) -> tuple:
    name = data.get('name', '').strip()
    if not name:
        return False, 'نام گیاه نمی‌تواند خالی باشد.'
    if len(name) < 2:
        return False, 'نام گیاه باید حداقل ۲ حرف داشته باشد.'
    return True, ''


def validate_timer_form(data: dict) -> tuple:
    name = data.get('name', '').strip()
    if not name:
        return False, 'نام تایمر نمی‌تواند خالی باشد.'
    interval = data.get('interval_days', 0)
    try:
        interval = int(interval)
    except Exception:
        return False, 'فاصله زمانی باید عدد باشد.'
    if interval < 1:
        return False, 'فاصله زمانی باید حداقل ۱ روز باشد.'
    return True, ''


CATEGORY_ICON = {
    'آپارتمانی': 'ic_leaf',
    'گلدار':      'ic_flower',
    'دارویی':     'ic_herb',
    'درخت میوه': 'ic_fruit',
}

def category_icon(cat: str) -> str:
    return CATEGORY_ICON.get(cat, 'ic_leaf')


def plant_summary(plant: dict) -> str:
    parts = []
    if plant.get('care_level'):
        parts.append(f"نگهداری: {plant['care_level']}")
    if plant.get('watering'):
        parts.append(f"آبیاری: {plant['watering']}")
    if plant.get('light'):
        parts.append(f"نور: {plant['light']}")
    return '  •  '.join(parts)

