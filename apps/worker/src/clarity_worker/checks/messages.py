from string import Formatter
from typing import NamedTuple


class Message(NamedTuple):
    title: str
    description: str
    recommendation: str


CATALOG: dict[str, dict[str, Message]] = {
    "low-contrast": {
        "en": Message(
            "Text contrast is too low",
            "“{text}” is {color} on {background}, a contrast of {ratio}:1. WCAG AA asks "
            "for at least {required}:1 at this size, so many visitors, especially on phones "
            "outdoors, will struggle to read it.",
            "Darken the text or lighten the background until the ratio reaches {required}:1.",
        ),
        "tr": Message(
            "Metin kontrastı çok düşük",
            "“{text}” {background} zemin üzerinde {color} renkte; kontrast {ratio}:1. WCAG AA "
            "bu boyut için en az {required}:1 ister; özellikle dışarıda telefon kullanan "
            "ziyaretçiler metni okumakta zorlanır.",
            "Oran {required}:1 olana kadar metni koyulaştırın ya da zemini açın.",
        ),
        "az": Message(
            "Mətnin kontrastı çox aşağıdır",
            "“{text}” {background} fon üzərində {color} rəngdədir; kontrast {ratio}:1. WCAG AA "
            "bu ölçü üçün ən azı {required}:1 tələb edir; xüsusilə çöldə telefondan baxan "
            "ziyarətçilər mətni çətin oxuyacaq.",
            "Nisbət {required}:1 olana qədər mətni tündləşdirin və ya fonu açın.",
        ),
        "ru": Message(
            "Слишком низкий контраст текста",
            "«{text}» - цвет {color} на фоне {background}, контраст {ratio}:1. WCAG AA требует "
            "не менее {required}:1 для такого размера, поэтому многим посетителям, особенно "
            "с телефона на улице, будет трудно его прочитать.",
            "Затемните текст или осветлите фон, пока контраст не достигнет {required}:1.",
        ),
    },
    "small-tap-target": {
        "en": Message(
            "Touch target is too small",
            "“{text}” is {width}×{height}px on {viewport}. Targets under 24×24px are easy to "
            "miss with a finger and fail WCAG 2.2 target size.",
            "Give it at least 44×44px of tappable area with padding, keeping the visual size if "
            "needed.",
        ),
        "tr": Message(
            "Dokunma alanı çok küçük",
            "“{text}” {viewport} görünümünde {width}×{height}px. 24×24px altındaki hedefler "
            "parmakla kolayca ıskalanır ve WCAG 2.2 hedef boyutu kuralını karşılamaz.",
            "Görsel boyutu korusanız bile dolguyla en az 44×44px dokunulabilir alan verin.",
        ),
        "az": Message(
            "Toxunma sahəsi çox kiçikdir",
            "“{text}” {viewport} görünüşündə {width}×{height}px-dir. 24×24px-dən kiçik "
            "hədəflərə barmaqla asanlıqla toxunmaq olmur və WCAG 2.2 hədəf ölçüsü qaydasına "
            "uyğun deyil.",
            "Vizual ölçünü saxlasanız belə, padding ilə ən azı 44×44px toxunma sahəsi verin.",
        ),
        "ru": Message(
            "Слишком маленькая область нажатия",
            "«{text}» на {viewport} - {width}×{height}px. Цели меньше 24×24px легко промахнуть "
            "пальцем, и они не проходят требование WCAG 2.2 к размеру цели.",
            "Сделайте область нажатия не меньше 44×44px за счёт отступов, визуальный размер "
            "можно сохранить.",
        ),
    },
    "missing-alt": {
        "en": Message(
            "Image has no alternative text",
            "This {width}×{height}px image ({src}) has no alt attribute, so screen readers "
            "announce the file name or skip it and search engines learn nothing from it.",
            'Add an alt text that says what the image shows, or alt="" if it is purely decorative.',
        ),
        "tr": Message(
            "Görselin alternatif metni yok",
            "{width}×{height}px boyutundaki bu görselde ({src}) alt özniteliği yok; ekran "
            "okuyucular dosya adını okur ya da görseli atlar, arama motorları da bir şey "
            "öğrenemez.",
            "Görselin ne gösterdiğini anlatan bir alt metni ekleyin; tamamen süs amaçlıysa "
            'alt="" kullanın.',
        ),
        "az": Message(
            "Şəklin alternativ mətni yoxdur",
            "{width}×{height}px ölçülü bu şəkildə ({src}) alt atributu yoxdur; ekran oxuyucular "
            "fayl adını oxuyur və ya şəkli ötürür, axtarış sistemləri də ondan heç nə "
            "öyrənmir.",
            "Şəklin nə göstərdiyini izah edən alt mətni əlavə edin; yalnız bəzək üçündürsə, "
            'alt="" yazın.',
        ),
        "ru": Message(
            "У изображения нет альтернативного текста",
            "У изображения {width}×{height}px ({src}) нет атрибута alt: программы экранного "
            "доступа читают имя файла или пропускают его, а поисковики ничего о нём не узнают.",
            'Добавьте alt с описанием того, что изображено, или alt="", если картинка '
            "чисто декоративная.",
        ),
    },
    "broken-image": {
        "en": Message(
            "Image fails to load",
            "The image {src} did not load ({reason}); visitors see an empty box or a broken "
            "icon in its place.",
            "Fix the file path or upload the missing file, and serve a placeholder when an image "
            "is unavailable.",
        ),
        "tr": Message(
            "Görsel yüklenmiyor",
            "{src} görseli yüklenemedi ({reason}); ziyaretçiler yerinde boş bir kutu ya da "
            "kırık simge görüyor.",
            "Dosya yolunu düzeltin ya da eksik dosyayı yükleyin; görsel yoksa yer tutucu gösterin.",
        ),
        "az": Message(
            "Şəkil yüklənmir",
            "{src} şəkli yüklənmədi ({reason}); ziyarətçilər onun yerində boş qutu və ya "
            "qırıq ikon görür.",
            "Fayl yolunu düzəldin və ya çatışmayan faylı yükləyin; şəkil olmadıqda yer tutucu "
            "göstərin.",
        ),
        "ru": Message(
            "Изображение не загружается",
            "Изображение {src} не загрузилось ({reason}); посетители видят на его месте пустой "
            "блок или значок ошибки.",
            "Исправьте путь к файлу или загрузите отсутствующий файл и показывайте заглушку, "
            "если изображение недоступно.",
        ),
    },
    "failed-resource": {
        "en": Message(
            "Page resources fail to load",
            "{count} request(s) the page depends on failed, including: {items}.",
            "Restore or remove these resources; failing scripts and styles can break layout "
            "and behaviour.",
        ),
        "tr": Message(
            "Sayfa kaynakları yüklenmiyor",
            "Sayfanın ihtiyaç duyduğu {count} istek başarısız oldu, örneğin: {items}.",
            "Bu kaynakları geri getirin ya da kaldırın; yüklenmeyen script ve stiller düzeni "
            "ve davranışı bozabilir.",
        ),
        "az": Message(
            "Səhifə resursları yüklənmir",
            "Səhifənin asılı olduğu {count} sorğu uğursuz oldu, məsələn: {items}.",
            "Bu resursları bərpa edin və ya silin; yüklənməyən skript və stillər görünüşü və "
            "davranışı poza bilər.",
        ),
        "ru": Message(
            "Ресурсы страницы не загружаются",
            "Не выполнено {count} запрос(ов), от которых зависит страница, например: {items}.",
            "Восстановите или уберите эти ресурсы: неработающие скрипты и стили могут "
            "ломать вёрстку и поведение.",
        ),
    },
    "console-errors": {
        "en": Message(
            "JavaScript errors on load",
            "The page logged {count} error(s) while loading, for example: {items}. Features "
            "that depend on that code may silently not work.",
            "Fix the errors in the browser console; check the scripts mentioned first.",
        ),
        "tr": Message(
            "Yükleme sırasında JavaScript hataları",
            "Sayfa yüklenirken {count} hata kaydetti, örneğin: {items}. Bu koda bağlı "
            "özellikler sessizce çalışmıyor olabilir.",
            "Tarayıcı konsolundaki hataları düzeltin; önce adı geçen scriptlere bakın.",
        ),
        "az": Message(
            "Yüklənmə zamanı JavaScript xətaları",
            "Səhifə yüklənərkən {count} xəta qeydə aldı, məsələn: {items}. Bu koddan asılı "
            "funksiyalar səssizcə işləməyə bilər.",
            "Brauzer konsolundakı xətaları düzəldin; əvvəlcə adı çəkilən skriptlərə baxın.",
        ),
        "ru": Message(
            "Ошибки JavaScript при загрузке",
            "При загрузке страница записала {count} ошибок, например: {items}. Функции, "
            "зависящие от этого кода, могут молча не работать.",
            "Исправьте ошибки в консоли браузера, начиная с упомянутых скриптов.",
        ),
    },
    "error-status": {
        "en": Message(
            "Page responds with HTTP {status}",
            "Requesting {url} returned status {status}; visitors and search engines reach an "
            "error instead of content.",
            "Restore the page, redirect it to its replacement, or remove links that point to it.",
        ),
        "tr": Message(
            "Sayfa HTTP {status} döndürüyor",
            "{url} isteği {status} durumunu döndürdü; ziyaretçiler ve arama motorları içerik "
            "yerine hata görüyor.",
            "Sayfayı geri getirin, yenisine yönlendirin ya da ona giden bağlantıları kaldırın.",
        ),
        "az": Message(
            "Səhifə HTTP {status} qaytarır",
            "{url} sorğusu {status} statusu qaytardı; ziyarətçilər və axtarış sistemləri "
            "məzmun əvəzinə xəta görür.",
            "Səhifəni bərpa edin, yenisinə yönləndirin və ya ona aparan keçidləri silin.",
        ),
        "ru": Message(
            "Страница отвечает HTTP {status}",
            "Запрос {url} вернул статус {status}; посетители и поисковики видят ошибку вместо "
            "содержимого.",
            "Восстановите страницу, перенаправьте на замену или уберите ссылки на неё.",
        ),
    },
    "missing-lang": {
        "en": Message(
            "Page language is not declared",
            "The <html> element has no lang attribute, so screen readers may pronounce the "
            "text with the wrong voice and translation tools guess the language.",
            'Add lang to <html>, for example lang="{suggested}".',
        ),
        "tr": Message(
            "Sayfa dili belirtilmemiş",
            "<html> öğesinde lang özniteliği yok; ekran okuyucular metni yanlış sesle "
            "okuyabilir, çeviri araçları dili tahmin etmek zorunda kalır.",
            '<html> öğesine lang ekleyin, örneğin lang="{suggested}".',
        ),
        "az": Message(
            "Səhifənin dili göstərilməyib",
            "<html> elementində lang atributu yoxdur; ekran oxuyucular mətni səhv səslə oxuya, "
            "tərcümə alətləri isə dili təxmin etməli ola bilər.",
            '<html> elementinə lang əlavə edin, məsələn lang="{suggested}".',
        ),
        "ru": Message(
            "Язык страницы не указан",
            "У элемента <html> нет атрибута lang, поэтому экранные чтецы могут читать текст "
            "не тем голосом, а переводчики - угадывать язык.",
            'Добавьте lang к <html>, например lang="{suggested}".',
        ),
    },
    "missing-viewport": {
        "en": Message(
            "No mobile viewport set",
            'The page has no <meta name="viewport">, so phones render it at desktop width '
            "and shrink it, making text tiny and forcing visitors to zoom.",
            'Add <meta name="viewport" content="width=device-width, initial-scale=1">.',
        ),
        "tr": Message(
            "Mobil viewport tanımlı değil",
            'Sayfada <meta name="viewport"> yok; telefonlar sayfayı masaüstü genişliğinde '
            "çizip küçültür, metin minicik kalır ve ziyaretçi yakınlaştırmak zorunda kalır.",
            '<meta name="viewport" content="width=device-width, initial-scale=1"> ekleyin.',
        ),
        "az": Message(
            "Mobil viewport təyin edilməyib",
            'Səhifədə <meta name="viewport"> yoxdur; telefonlar səhifəni masaüstü enində '
            "çəkib kiçildir, mətn xırda qalır və ziyarətçi böyütməli olur.",
            '<meta name="viewport" content="width=device-width, initial-scale=1"> əlavə edin.',
        ),
        "ru": Message(
            "Не задан мобильный viewport",
            'На странице нет <meta name="viewport">, поэтому телефоны рисуют её в ширину '
            "десктопа и уменьшают: текст становится мелким, приходится масштабировать.",
            'Добавьте <meta name="viewport" content="width=device-width, initial-scale=1">.',
        ),
    },
    "no-h1": {
        "en": Message(
            "Page has no main heading",
            "There is no <h1>, so screen-reader users and search engines get no clear "
            "statement of what the page is about.",
            "Mark the page's main title up as a single <h1>.",
        ),
        "tr": Message(
            "Sayfanın ana başlığı yok",
            "Sayfada <h1> yok; ekran okuyucu kullananlar ve arama motorları sayfanın konusunu "
            "net olarak öğrenemez.",
            "Sayfanın ana başlığını tek bir <h1> olarak işaretleyin.",
        ),
        "az": Message(
            "Səhifənin əsas başlığı yoxdur",
            "Səhifədə <h1> yoxdur; ekran oxuyucu istifadəçiləri və axtarış sistemləri "
            "səhifənin nə haqda olduğunu aydın öyrənə bilmir.",
            "Səhifənin əsas başlığını tək <h1> kimi işarələyin.",
        ),
        "ru": Message(
            "У страницы нет главного заголовка",
            "На странице нет <h1>, поэтому пользователи экранных чтецов и поисковики не "
            "получают ясного указания, о чём она.",
            "Оформите главный заголовок страницы одним <h1>.",
        ),
    },
    "multiple-h1": {
        "en": Message(
            "Several main headings",
            "The page has {count} <h1> elements ({items}), which blurs what the page is "
            "primarily about.",
            "Keep one <h1> for the page title and demote the others to <h2>.",
        ),
        "tr": Message(
            "Birden çok ana başlık",
            "Sayfada {count} adet <h1> var ({items}); bu, sayfanın asıl konusunu bulanıklaştırır.",
            "Sayfa başlığı için tek bir <h1> bırakın, diğerlerini <h2> yapın.",
        ),
        "az": Message(
            "Bir neçə əsas başlıq",
            "Səhifədə {count} ədəd <h1> var ({items}); bu, səhifənin əsas mövzusunu "
            "bulanıqlaşdırır.",
            "Səhifə başlığı üçün tək <h1> saxlayın, qalanlarını <h2> edin.",
        ),
        "ru": Message(
            "Несколько главных заголовков",
            "На странице {count} элементов <h1> ({items}), из-за чего неясно, о чём она "
            "в первую очередь.",
            "Оставьте один <h1> для заголовка страницы, остальные сделайте <h2>.",
        ),
    },
    "slow-load": {
        "en": Message(
            "Page loads slowly",
            "The page took {seconds}s to finish loading on {viewport}. Visitors start "
            "leaving after about three seconds.",
            "Compress and lazy-load large images, defer non-critical scripts and cache static "
            "files.",
        ),
        "tr": Message(
            "Sayfa yavaş yükleniyor",
            "Sayfanın {viewport} görünümünde yüklenmesi {seconds} sn sürdü. Ziyaretçiler "
            "yaklaşık üç saniyeden sonra ayrılmaya başlar.",
            "Büyük görselleri sıkıştırıp tembel yükleyin, kritik olmayan scriptleri "
            "erteleyin ve statik dosyaları önbelleğe alın.",
        ),
        "az": Message(
            "Səhifə yavaş yüklənir",
            "Səhifənin {viewport} görünüşündə yüklənməsi {seconds} san çəkdi. Ziyarətçilər "
            "təxminən üç saniyədən sonra çıxmağa başlayır.",
            "Böyük şəkilləri sıxın və gecikmə ilə yükləyin, vacib olmayan skriptləri "
            "təxirə salın və statik faylları keşləyin.",
        ),
        "ru": Message(
            "Страница медленно загружается",
            "На {viewport} страница загружалась {seconds} с. Посетители начинают уходить уже "
            "примерно через три секунды.",
            "Сожмите и загружайте лениво крупные изображения, отложите второстепенные скрипты "
            "и кэшируйте статику.",
        ),
    },
}

VIEWPORT_NAMES = {
    "en": {"desktop": "desktop", "tablet": "tablet", "mobile": "mobile"},
    "tr": {"desktop": "masaüstü", "tablet": "tablet", "mobile": "mobil"},
    "az": {"desktop": "masaüstü", "tablet": "planşet", "mobile": "mobil"},
    "ru": {"desktop": "десктопе", "tablet": "планшете", "mobile": "мобильном"},
}


def message(key: str, language: str, **values: object) -> Message:
    template = CATALOG[key].get(language) or CATALOG[key]["en"]
    return Message(*(part.format(**values) for part in template))


def placeholders(key: str, language: str) -> set[str]:
    template = CATALOG[key][language]
    return {name for part in template for _, name, _, _ in Formatter().parse(part) if name}
