/**
 * پراکسی امن برای بخش «دستیار هوشمند» اپ گیاهیار (چت + تحلیل تصویر گیاه
 * با DeepSeek Vision).
 *
 * چرا این فایل لازم است؟
 * اپ اندروید (فایل APK) یک بسته عمومی است؛ هر متنی که داخل کد پایتون
 * قرار بگیرد - از جمله یک کلید API که در config.py گذاشته باشید - قابل
 * استخراج توسط هر کسی است که فایل APK را داشته باشد (چه از ریلیزهای
 * گیت‌هاب دانلود کند، چه مستقیم از گوشی). پس برای انتشار عمومیِ اپ، کلید
 * DeepSeek نباید داخل کد اپ باشد. این Worker به‌جای اپ، کلید را روی سرور
 * (Cloudflare) نگه می‌دارد؛ اپ فقط با خودِ این Worker حرف می‌زند، نه
 * مستقیم با DeepSeek.
 *
 * (اگر فقط دارید محلی تست می‌کنید یا اپ را عمومی منتشر نمی‌کنید، لازم
 * نیست از این فایل استفاده کنید - همان DEEPSEEK_API_KEY مستقیم در
 * config.py کافی است. جزئیات: docstring بالای config.py.)
 *
 * راه‌اندازی (رایگان، حدود ۵ دقیقه):
 *   ۱. یک حساب رایگان در https://dash.cloudflare.com بسازید.
 *   ۲. از منوی سمت چپ: Workers & Pages → Create → Create Worker.
 *      یک اسم بدهید (مثلاً plant-vet-proxy) و Deploy کنید.
 *   ۳. روی Worker ساخته‌شده → Edit code بروید و کل کد پیش‌فرض را با
 *      محتوای همین فایل جایگزین کنید → Deploy.
 *   ۴. برو به Settings → Variables and Secrets → Add:
 *        نام: DEEPSEEK_API_KEY   مقدار: کلید واقعی شما   نوع: Secret
 *      (کلید را از https://platform.deepseek.com می‌گیرید)
 *   ۵. (اختیاری ولی پیشنهادی) یک secret دوم هم اضافه کنید:
 *        نام: APP_SHARED_SECRET   مقدار: یک رشته دلخواه و طولانی
 *      این باعث می‌شود فقط اپ خودتان بتواند از این Worker استفاده کند،
 *      نه هر کسی که آدرس Worker را حدس بزند. (کلید اصلی DeepSeek را
 *      فاش نمی‌کند، فقط مصرفِ Worker شما را محدود می‌کند.)
 *   ۶. آدرس نهایی که Cloudflare نشان می‌دهد
 *      (شبیه https://plant-vet-proxy.YOUR-SUBDOMAIN.workers.dev) را
 *      کپی کنید و در config.py مقدار PROXY_URL قرار دهید (و اگر مرحله ۵
 *      را انجام دادید، همان رشته را در APP_SHARED_SECRET همان فایل هم
 *      بگذارید). وقتی PROXY_URL پر باشد، ai_vet_screen.py خودکار به‌جای
 *      تماس مستقیم، از همین پراکسی استفاده می‌کند.
 *
 * نکته امنیتی اضافه (اختیاری): در داشبورد Cloudflare، بخش
 * Security → WAF → Rate limiting rules، می‌توانید بدون نوشتن کد یک
 * محدودیت مثل «حداکثر ۲۰ درخواست در دقیقه از هر IP» هم اضافه کنید.
 */

const ALLOWED_MODEL_PREFIX = 'deepseek-';
const DEEPSEEK_URL = 'https://api.deepseek.com/chat/completions';

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-App-Secret',
  };
}

function jsonResponse(obj, status, extraHeaders) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...corsHeaders(), 'Content-Type': 'application/json', ...(extraHeaders || {}) },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    if (request.method !== 'POST') {
      return jsonResponse({ error: 'method not allowed' }, 405);
    }

    if (!env.DEEPSEEK_API_KEY) {
      return jsonResponse(
        { error: 'DEEPSEEK_API_KEY تنظیم نشده - آن را در Settings > Variables and Secrets اضافه کنید' },
        500
      );
    }

    // اگر APP_SHARED_SECRET تنظیم شده، فقط درخواست‌هایی که همان مقدار را
    // در هدر X-App-Secret بفرستند قبول می‌شوند
    if (env.APP_SHARED_SECRET) {
      const provided = request.headers.get('X-App-Secret');
      if (provided !== env.APP_SHARED_SECRET) {
        return jsonResponse({ error: 'unauthorized' }, 401);
      }
    }

    let payload;
    try {
      payload = await request.json();
    } catch (err) {
      return jsonResponse({ error: 'invalid JSON body' }, 400);
    }

    if (typeof payload.model !== 'string' || !payload.model.startsWith(ALLOWED_MODEL_PREFIX)) {
      return jsonResponse({ error: 'invalid or missing "model" field' }, 400);
    }
    if (!Array.isArray(payload.messages)) {
      return jsonResponse({ error: 'invalid or missing "messages" field' }, 400);
    }

    try {
      const upstream = await fetch(DEEPSEEK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.DEEPSEEK_API_KEY}`,
        },
        body: JSON.stringify(payload),
      });

      const responseBody = await upstream.text();
      return new Response(responseBody, {
        status: upstream.status,
        headers: { ...corsHeaders(), 'Content-Type': 'application/json' },
      });
    } catch (err) {
      return jsonResponse({ error: String(err) }, 502);
    }
  },
};
