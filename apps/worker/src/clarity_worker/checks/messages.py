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
    "horizontal-overflow": {
        "en": Message(
            "The page scrolls sideways on {viewport}",
            "The page is {width}px wide on a {viewport} screen of {screen}px, so visitors can "
            "drag it sideways and content gets cut off. The widest element starts here: {culprit}.",
            "Constrain that element with max-width: 100%, let tables and code scroll inside their "
            "own container, and avoid fixed widths wider than the screen.",
        ),
        "tr": Message(
            "Sayfa {viewport} görünümünde yana kayıyor",
            "{screen}px genişliğindeki {viewport} ekranda sayfa {width}px genişliğinde; ziyaretçi "
            "sayfayı yana sürükleyebiliyor ve içerik kesiliyor. En geniş öğe burada: {culprit}.",
            "Bu öğeyi max-width: 100% ile sınırlayın, tabloları ve kodu kendi kapsayıcısında "
            "kaydırın, ekrandan geniş sabit genişliklerden kaçının.",
        ),
        "az": Message(
            "Səhifə {viewport} görünüşündə yana sürüşür",
            "{screen}px enində {viewport} ekranda səhifənin eni {width}px-dir; ziyarətçi səhifəni "
            "yana çəkə bilir və məzmun kəsilir. Ən geniş element buradadır: {culprit}.",
            "Bu elementi max-width: 100% ilə məhdudlaşdırın, cədvəlləri və kodu öz "
            "konteynerində sürüşdürün, ekrandan geniş sabit enlərdən çəkinin.",
        ),
        "ru": Message(
            "Страница прокручивается вбок на {viewport}",
            "На экране {viewport} шириной {screen}px страница занимает {width}px: её можно "
            "сдвинуть вбок, и содержимое обрезается. Самый широкий элемент: {culprit}.",
            "Ограничьте этот элемент max-width: 100%, прокручивайте таблицы и код внутри "
            "своего контейнера и избегайте фиксированной ширины больше экрана.",
        ),
    },
    "search-no-effect": {
        "en": Message(
            "Searching does nothing",
            "We typed “{query}” into the search field and submitted it: no results page, no "
            "change on the page and no request. Visitors who rely on search are stuck.",
            "Connect the search form to a results page or a search request, and show a "
            "message when nothing matches.",
        ),
        "tr": Message(
            "Arama hiçbir şey yapmıyor",
            "Arama alanına “{query}” yazıp gönderdik: sonuç sayfası yok, sayfada değişiklik yok, "
            "istek yok. Aramaya güvenen ziyaretçi takılıp kalıyor.",
            "Arama formunu bir sonuç sayfasına ya da arama isteğine bağlayın, eşleşme yoksa "
            "bunu bildiren bir mesaj gösterin.",
        ),
        "az": Message(
            "Axtarış heç nə etmir",
            "Axtarış sahəsinə “{query}” yazıb göndərdik: nəticə səhifəsi, səhifədə dəyişiklik və "
            "sorğu yoxdur. Axtarışa güvənən ziyarətçi ilişib qalır.",
            "Axtarış formasını nəticə səhifəsinə və ya axtarış sorğusuna bağlayın, uyğunluq "
            "olmadıqda bunu bildirən mesaj göstərin.",
        ),
        "ru": Message(
            "Поиск ничего не делает",
            "Мы ввели «{query}» в поле поиска и отправили: ни страницы результатов, ни "
            "изменений на странице, ни запроса. Посетитель, полагающийся на поиск, застревает.",
            "Свяжите форму поиска со страницей результатов или запросом и показывайте "
            "сообщение, если ничего не найдено.",
        ),
    },
    "form-accepts-empty": {
        "en": Message(
            "“{form}” sends with every field empty",
            "Submitting the form with nothing filled in went straight to the server; nothing "
            "on the page told the visitor what was missing. The request was stopped by the "
            "auditor and never reached the site.",
            "Mark required fields with required or validate before sending, and show a clear "
            "message next to each missing field.",
        ),
        "tr": Message(
            "“{form}” tüm alanlar boşken gönderiliyor",
            "Hiçbir alan doldurulmadan gönderilen form doğrudan sunucuya gitti; sayfada eksik "
            "olanı söyleyen bir şey yoktu. İstek denetçi tarafından durduruldu, siteye ulaşmadı.",
            "Zorunlu alanları required ile işaretleyin ya da göndermeden önce doğrulayın, her "
            "eksik alanın yanında açık bir mesaj gösterin.",
        ),
        "az": Message(
            "“{form}” bütün sahələr boş ikən göndərilir",
            "Heç bir sahə doldurulmadan göndərilən forma birbaşa serverə getdi; səhifədə nəyin "
            "çatışmadığını deyən heç nə yox idi. Sorğu yoxlayıcı tərəfindən dayandırıldı, sayta "
            "çatmadı.",
            "Məcburi sahələri required ilə işarələyin və ya göndərmədən əvvəl yoxlayın, hər "
            "çatışmayan sahənin yanında aydın mesaj göstərin.",
        ),
        "ru": Message(
            "«{form}» отправляется с пустыми полями",
            "Форма без единого заполненного поля сразу ушла на сервер, и на странице не "
            "появилось ничего о том, чего не хватает. Запрос был остановлен аудитом и до "
            "сайта не дошёл.",
            "Отметьте обязательные поля атрибутом required или проверяйте их перед "
            "отправкой и показывайте понятное сообщение у каждого пустого поля.",
        ),
    },
    "no-effect": {
        "en": Message(
            "Clicking “{text}” does nothing",
            "We clicked it in a real browser and nothing happened: no navigation, no change to "
            "the page, no request, no dialog and no scroll. Visitors who try it will think the "
            "site is broken.",
            "Wire the control to its action, or remove it if it has none. If it should open "
            "something, check its event handler and the console.",
        ),
        "tr": Message(
            "“{text}” tıklanınca hiçbir şey olmuyor",
            "Gerçek bir tarayıcıda tıkladık ve hiçbir şey olmadı: yönlendirme, sayfa "
            "değişikliği, istek, diyalog ya da kaydırma yok. Deneyen ziyaretçi sitenin bozuk "
            "olduğunu düşünür.",
            "Kontrolü eylemine bağlayın ya da işlevi yoksa kaldırın. Bir şey açması gerekiyorsa "
            "olay dinleyicisini ve konsolu kontrol edin.",
        ),
        "az": Message(
            "“{text}” kliklənəndə heç nə baş vermir",
            "Real brauzerdə kliklədik və heç nə baş vermədi: keçid, səhifədə dəyişiklik, sorğu, "
            "dialoq və ya sürüşmə yoxdur. Sınayan ziyarətçi saytın xarab olduğunu düşünəcək.",
            "İdarəetmə elementini öz əməliyyatına bağlayın və ya funksiyası yoxdursa silin. Nəsə "
            "açmalıdırsa, hadisə dinləyicisini və konsolu yoxlayın.",
        ),
        "ru": Message(
            "Нажатие на «{text}» ничего не делает",
            "Мы нажали на элемент в настоящем браузере, и ничего не произошло: ни перехода, ни "
            "изменений на странице, ни запроса, ни диалога, ни прокрутки. Посетитель решит, что "
            "сайт сломан.",
            "Привяжите элемент к действию или уберите его, если действия нет. Если он должен "
            "что-то открывать, проверьте обработчик события и консоль.",
        ),
    },
    "click-error": {
        "en": Message(
            "Clicking “{text}” throws an error",
            "Clicking it raised a JavaScript error: “{error}”. Whatever it was meant to do "
            "did not finish.",
            "Fix the error in the click handler; the message points to the failing call.",
        ),
        "tr": Message(
            "“{text}” tıklanınca hata oluşuyor",
            "Tıklama bir JavaScript hatasına yol açtı: “{error}”. Yapması gereken işlem "
            "tamamlanmadı.",
            "Tıklama işleyicisindeki hatayı düzeltin; mesaj başarısız çağrıyı gösteriyor.",
        ),
        "az": Message(
            "“{text}” kliklənəndə xəta yaranır",
            "Klik JavaScript xətasına səbəb oldu: “{error}”. Görməli olduğu iş tamamlanmadı.",
            "Klik işləyicisindəki xətanı düzəldin; mesaj uğursuz çağırışı göstərir.",
        ),
        "ru": Message(
            "Нажатие на «{text}» вызывает ошибку",
            "Нажатие привело к ошибке JavaScript: «{error}». Действие не завершилось.",
            "Исправьте ошибку в обработчике нажатия; сообщение указывает на сбойный вызов.",
        ),
    },
    "anchor-missing": {
        "en": Message(
            "“{text}” points to a section that does not exist",
            "The link goes to #{target}, but no element on the page has that id, so clicking "
            "it leaves the visitor where they were.",
            'Give the intended section id="{target}" or change the link to an existing id.',
        ),
        "tr": Message(
            "“{text}” var olmayan bir bölüme gidiyor",
            "Bağlantı #{target} adresine gidiyor ama sayfada bu id'ye sahip bir öğe yok; "
            "tıklayan ziyaretçi olduğu yerde kalıyor.",
            'Hedef bölüme id="{target}" verin ya da bağlantıyı var olan bir id\'ye çevirin.',
        ),
        "az": Message(
            "“{text}” mövcud olmayan bölməyə aparır",
            "Keçid #{target} ünvanına aparır, amma səhifədə bu id-yə malik element yoxdur; "
            "klikləyən ziyarətçi olduğu yerdə qalır.",
            'Hədəf bölməyə id="{target}" verin və ya keçidi mövcud id-yə dəyişin.',
        ),
        "ru": Message(
            "«{text}» ведёт к несуществующему разделу",
            "Ссылка ведёт на #{target}, но на странице нет элемента с таким id, и посетитель "
            "остаётся на месте.",
            'Задайте нужному разделу id="{target}" или поменяйте ссылку на существующий id.',
        ),
    },
    "broken-link": {
        "en": Message(
            "“{text}” leads to an error page",
            "The link points to {url}, which answers HTTP {status}.",
            "Update the link to the right address or restore the page it points to.",
        ),
        "tr": Message(
            "“{text}” hata sayfasına gidiyor",
            "Bağlantı {url} adresine gidiyor ve bu adres HTTP {status} döndürüyor.",
            "Bağlantıyı doğru adrese güncelleyin ya da gittiği sayfayı geri getirin.",
        ),
        "az": Message(
            "“{text}” xəta səhifəsinə aparır",
            "Keçid {url} ünvanına aparır və bu ünvan HTTP {status} qaytarır.",
            "Keçidi düzgün ünvana yeniləyin və ya apardığı səhifəni bərpa edin.",
        ),
        "ru": Message(
            "«{text}» ведёт на страницу ошибки",
            "Ссылка ведёт на {url}, а этот адрес отвечает HTTP {status}.",
            "Исправьте адрес ссылки или восстановите страницу, на которую она ведёт.",
        ),
    },
    "menu-no-close": {
        "en": Message(
            "“{text}” opens but will not close",
            "Clicking it opened a menu or panel; clicking it again and pressing Escape left it "
            "open, so visitors can get stuck with it covering the page.",
            "Let the same control close it, close it on Escape and on outside clicks, and keep "
            "aria-expanded in sync.",
        ),
        "tr": Message(
            "“{text}” açılıyor ama kapanmıyor",
            "Tıklayınca bir menü ya da panel açıldı; tekrar tıklamak ve Escape'e basmak onu "
            "kapatmadı, ziyaretçi sayfayı kapatan bu panelle kalabiliyor.",
            "Aynı kontrolle kapanmasını sağlayın, Escape ve dışarı tıklamayla kapatın, "
            "aria-expanded değerini güncel tutun.",
        ),
        "az": Message(
            "“{text}” açılır, amma bağlanmır",
            "Klikləyəndə menyu və ya panel açıldı; yenidən klikləmək və Escape düyməsi onu "
            "bağlamadı, ziyarətçi səhifəni örtən bu panellə qala bilər.",
            "Eyni elementlə bağlanmasını təmin edin, Escape və kənara kliklə bağlayın, "
            "aria-expanded dəyərini aktual saxlayın.",
        ),
        "ru": Message(
            "«{text}» открывается, но не закрывается",
            "Нажатие открыло меню или панель; повторное нажатие и Escape её не закрыли, и "
            "посетитель может застрять с панелью поверх страницы.",
            "Дайте тому же элементу закрывать её, закрывайте по Escape и клику снаружи, "
            "обновляйте aria-expanded.",
        ),
    },
    "dialog-no-close": {
        "en": Message(
            "The dialog opened by “{text}” cannot be closed",
            "A dialog appeared after clicking it; neither Escape nor a visible close button "
            "dismissed it.",
            "Add a visible close button and close the dialog on Escape.",
        ),
        "tr": Message(
            "“{text}” ile açılan diyalog kapatılamıyor",
            "Tıklamadan sonra bir diyalog açıldı; ne Escape ne de görünen bir kapatma düğmesi "
            "onu kapattı.",
            "Görünür bir kapatma düğmesi ekleyin ve diyaloğu Escape ile kapatın.",
        ),
        "az": Message(
            "“{text}” ilə açılan dialoq bağlanmır",
            "Klikdən sonra dialoq açıldı; nə Escape, nə də görünən bağlama düyməsi onu bağladı.",
            "Görünən bağlama düyməsi əlavə edin və dialoqu Escape ilə bağlayın.",
        ),
        "ru": Message(
            "Диалог, открытый «{text}», не закрывается",
            "После нажатия появился диалог; ни Escape, ни видимая кнопка закрытия его не закрыли.",
            "Добавьте видимую кнопку закрытия и закрывайте диалог по Escape.",
        ),
    },
    "language-partial": {
        "en": Message(
            "Language switch “{text}” barely changes the page",
            "After switching, only {changed}% of the visible text changed and the page language "
            "stayed {lang}. Visitors who chose another language still read the original.",
            "Translate the whole page when the language changes, or link to the translated "
            "version of the page.",
        ),
        "tr": Message(
            "Dil değiştirici “{text}” sayfayı neredeyse hiç değiştirmiyor",
            "Değiştirdikten sonra görünen metnin yalnızca %{changed} kadarı değişti ve sayfa "
            "dili {lang} kaldı. Başka dil seçen ziyaretçi hâlâ orijinal metni okuyor.",
            "Dil değiştiğinde tüm sayfayı çevirin ya da sayfanın çevrilmiş sürümüne bağlantı "
            "verin.",
        ),
        "az": Message(
            "Dil dəyişdirici “{text}” səhifəni demək olar ki, dəyişmir",
            "Dəyişdikdən sonra görünən mətnin yalnız {changed}%-i dəyişdi və səhifənin dili "
            "{lang} qaldı. Başqa dil seçən ziyarətçi hələ də orijinal mətni oxuyur.",
            "Dil dəyişəndə bütün səhifəni tərcümə edin və ya səhifənin tərcümə olunmuş "
            "versiyasına keçid verin.",
        ),
        "ru": Message(
            "Переключатель языка «{text}» почти не меняет страницу",
            "После переключения изменилось лишь {changed}% видимого текста, а язык страницы "
            "остался {lang}. Посетитель, выбравший другой язык, читает исходный текст.",
            "Переводите всю страницу при смене языка или ведите на переведённую версию страницы.",
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
