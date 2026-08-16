/*
 * COSMOS — Internationalization (i18n)
 * ---------------------------------------------------------------------------
 * Ten languages, live switching, persisted choice, graceful missing-key
 * fallback to English. Keys are flat dotted strings for trivial lookup.
 *
 *   I18n.langs            -> {code: nativeName}
 *   I18n.get(code?)       -> current code
 *   I18n.set(code)        -> switch + persist + dispatch 'langchange'
 *   I18n.t(key, vars?)    -> translate (supports {name} interpolation)
 *   I18n.apply(root)      -> walk DOM for data-i18n / data-i18n-attr
 *
 * Languages: English, 中文, Português, Español, 한국어, Français,
 *            Deutsch, 日本語, العربية, Русский
 */
(function (global) {
  "use strict";

  var langs = {
    en: "English", zh: "中文", pt: "Português", es: "Español",
    ko: "한국어", fr: "Français", de: "Deutsch", ja: "日本語",
    ar: "العربية", ru: "Русский"
  };

  // RTL languages
  var rtl = { ar: true };

  var STRINGS = {
    "app.title": {
      en: "COSMOS", zh: "宇宙", pt: "COSMOS", es: "COSMOS", ko: "코스모스",
      fr: "COSMOS", de: "KOSMOS", ja: "コスモス", ar: "كوزموس", ru: "КОСМОС" },
    "app.tagline": {
      en: "An interactive explorer for NASA's open data", 
      zh: "NASA 开放数据的交互式探索器",
      pt: "Um explorador interativo dos dados abertos da NASA",
      es: "Un explorador interactivo de los datos abiertos de la NASA",
      ko: "NASA 공개 데이터를 위한 인터랙티브 탐색기",
      fr: "Un explorateur interactif des données ouvertes de la NASA",
      de: "Ein interaktiver Explorer für offene NASA-Daten",
      ja: "NASAのオープンデータのためのインタラクティブな探検機",
      ar: "مستكشف تفاعلي للبيانات المفتوحة للناسا",
      ru: "Интерактивный исследователь открытых данных NASA" },

    "nav.explore": { en: "Explore", zh: "探索", pt: "Explorar", es: "Explorar",
      ko: "탐험", fr: "Explorer", de: "Erkunden", ja: "探索", ar: "استكشف", ru: "Исследовать" },
    "nav.apod": { en: "Picture of the Day", zh: "每日天文一图", pt: "Imagem do Dia",
      es: "Imagen del Día", ko: "오늘의 사진", fr: "Image du Jour", de: "Bild des Tages",
      ja: "今日の一枚", ar: "صورة اليوم", ru: "Фото дня" },
    "nav.mars": { en: "Mars Rovers", zh: "火星探测车", pt: "Rovers de Marte",
      es: "Rovers de Marte", ko: "화성 탐사차", fr: "Rovers Martiens", de: "Mars-Rover",
      ja: "火星ローバー", ar: "مركبات المريخ", ru: "Марсоходы" },
    "nav.neo": { en: "Asteroids", zh: "小行星", pt: "Asteroides", es: "Asteroides",
      ko: "소행성", fr: "Astéroïdes", de: "Asteroiden", ja: "小惑星", ar: "الكويكبات", ru: "Астероиды" },
    "nav.epic": { en: "Earth Live", zh: "地球实况", pt: "Terra ao Vivo", es: "Tierra en Vivo",
      ko: "지구 실시간", fr: "Terre en Direct", de: "Erde Live", ja: "地球ライブ", ar: "الأرض مباشر", ru: "Земля вживую" },
    "nav.weather": { en: "Space Weather", zh: "太空天气", pt: "Clima Espacial",
      es: "Clima Espacial", ko: "우주 날씨", fr: "Météo Spatiale", de: "Weltraumwetter",
      ja: "宇宙天気", ar: "طقس الفضاء", ru: "Космическая погода" },
    "nav.tech": { en: "Spinoffs", zh: "技术转化", pt: "Tecnologias", es: "Tecnologías",
      ko: "파생기술", fr: " retombées", de: "Spin-offs", ja: "スピンオフ", ar: "التقنيات", ru: "Технологии" },
    "nav.settings": { en: "Settings", zh: "设置", pt: "Configurações", es: "Ajustes",
      ko: "설정", fr: "Réglages", de: "Einstellungen", ja: "設定", ar: "الإعدادات", ru: "Настройки" },

    "explore.heading": { en: "The Solar System, in real time", 
      zh: "实时太阳系", pt: "O Sistema Solar, em tempo real",
      es: "El Sistema Solar, en tiempo real", ko: "실시간 태양계",
      fr: "Le Système Solaire, en temps réel", de: "Das Sonnensystem, in Echtzeit",
      ja: "リアルタイムの太陽系", ar: "النظام الشمسي في الوقت الفعلي", 
      ru: "Солнечная система в реальном времени" },
    "explore.hint": { en: "Drag to orbit · Scroll to zoom · Click a body to inspect",
      zh: "拖动旋转 · 滚轮缩放 · 点击天体查看详情",
      pt: "Arraste para orbitar · Rola para zoom · Clique num corpo para inspecionar",
      es: "Arrastra para orbitar · Rueda para zoom · Clic en un cuerpo",
      ko: "드래그로 공전 · 스크롤로 확대 · 클릭으로 확인",
      fr: "Glisser pour orbiter · Molette pour zoomer · Clic pour inspecter",
      de: "Ziehen zum Orbiten · Scrollen zum Zoomen · Klick zum Inspizieren",
      ja: "ドラッグで周回 · スクロールでズーム · クリックで詳細",
      ar: "اسحب للدوران · مرر للتكبير · انقر للفحص",
      ru: "Тяните для орбиты · Колесо для зума · Клик по телу" },

    "body.sun": { en: "Sun", zh: "太阳", pt: "Sol", es: "Sol", ko: "태양", fr: "Soleil",
      de: "Sonne", ja: "太陽", ar: "الشمس", ru: "Солнце" },
    "body.mercury": { en: "Mercury", zh: "水星", pt: "Mercúrio", es: "Mercurio",
      ko: "수성", fr: "Mercure", de: "Merkur", ja: "水星", ar: "عطارد", ru: "Меркурий" },
    "body.venus": { en: "Venus", zh: "金星", pt: "Vénus", es: "Venus", ko: "금성",
      fr: "Vénus", de: "Venus", ja: "金星", ar: "الزهرة", ru: "Венера" },
    "body.earth": { en: "Earth", zh: "地球", pt: "Terra", es: "Tierra", ko: "지구",
      fr: "Terre", de: "Erde", ja: "地球", ar: "الأرض", ru: "Земля" },
    "body.mars": { en: "Mars", zh: "火星", pt: "Marte", es: "Marte", ko: "화성",
      fr: "Mars", de: "Mars", ja: "火星", ar: "المريخ", ru: "Марс" },
    "body.jupiter": { en: "Jupiter", zh: "木星", pt: "Júpiter", es: "Júpiter", ko: "목성",
      fr: "Jupiter", de: "Jupiter", ja: "木星", ar: "المشتري", ru: "Юпитер" },
    "body.saturn": { en: "Saturn", zh: "土星", pt: "Saturno", es: "Saturno", ko: "토성",
      fr: "Saturne", de: "Saturn", ja: "土星", ar: "زحل", ru: "Сатурн" },
    "body.uranus": { en: "Uranus", zh: "天王星", pt: "Úrano", es: "Urano", ko: "천왕성",
      fr: "Uranus", de: "Uranus", ja: "天王星", ar: "أورانوس", ru: "Уран" },
    "body.neptune": { en: "Neptune", zh: "海王星", pt: "Netuno", es: "Neptuno", ko: "해왕성",
      fr: "Neptune", de: "Neptun", ja: "海王星", ar: "نبتون", ru: "Нептун" },
    "body.moon": { en: "Moon", zh: "月球", pt: "Lua", es: "Luna", ko: "달", fr: "Lune",
      de: "Mond", ja: "月", ar: "القمر", ru: "Луна" },

    "action.run": { en: "Run", zh: "运行", pt: "Executar", es: "Ejecutar", ko: "실행",
      fr: "Lancer", de: "Starten", ja: "実行", ar: "تشغيل", ru: "Запустить" },
    "action.export.image": { en: "Export Image", zh: "导出图像", pt: "Exportar Imagem",
      es: "Exportar Imagen", ko: "이미지 내보내기", fr: "Exporter l'Image",
      de: "Bild exportieren", ja: "画像をエクスポート", ar: "تصدير الصورة", ru: "Экспорт изображения" },
    "action.record": { en: "Record Video", zh: "录制视频", pt: "Gravar Vídeo",
      es: "Grabar Vídeo", ko: "비디오 녹화", fr: "Enregistrer", de: "Video aufnehmen",
      ja: "ビデオ録画", ar: "تسجيل الفيديو", ru: "Запись видео" },
    "action.stop": { en: "Stop", zh: "停止", pt: "Parar", es: "Detener", ko: "정지",
      fr: "Arrêter", de: "Stopp", ja: "停止", ar: "إيقاف", ru: "Стоп" },
    "action.screenshot": { en: "Screenshot", zh: "截图", pt: "Captura de Ecrã",
      es: "Captura", ko: "스크린샷", fr: "Capture", de: "Screenshot", ja: "スクリーンショット",
      ar: "لقطة شاشة", ru: "Снимок" },

    "quality.label": { en: "Quality", zh: "画质", pt: "Qualidade", es: "Calidad",
      ko: "화질", fr: "Qualité", de: "Qualität", ja: "品質", ar: "الجودة", ru: "Качество" },
    "quality.high": { en: "High", zh: "高", pt: "Alta", es: "Alta", ko: "높음",
      fr: "Haute", de: "Hoch", ja: "高", ar: "عالية", ru: "Высокое" },
    "quality.medium": { en: "Medium", zh: "中", pt: "Média", es: "Media", ko: "중간",
      fr: "Moyenne", de: "Mittel", ja: "中", ar: "متوسطة", ru: "Среднее" },
    "quality.low": { en: "Low", zh: "低", pt: "Baixa", es: "Baja", ko: "낮음",
      fr: "Basse", de: "Niedrig", ja: "低", ar: "منخفضة", ru: "Низкое" },

    "sound.label": { en: "Sound", zh: "声音", pt: "Som", es: "Sonido", ko: "소리",
      fr: "Son", de: "Ton", ja: "サウンド", ar: "الصوت", ru: "Звук" },
    "sound.on": { en: "On", zh: "开", pt: "Ligado", es: "Activado", ko: "켜짐",
      fr: "Activé", de: "An", ja: "オン", ar: "تشغيل", ru: "Вкл" },
    "sound.off": { en: "Off", zh: "关", pt: "Desligado", es: "Desactivado", ko: "꺼짐",
      fr: "Désactivé", de: "Aus", ja: "オフ", ar: "إيقاف", ru: "Выкл" },

    "settings.heading": { en: "Settings", zh: "设置", pt: "Configurações", es: "Ajustes",
      ko: "설정", fr: "Réglages", de: "Einstellungen", ja: "設定", ar: "الإعدادات", ru: "Настройки" },
    "settings.apikey": { en: "NASA API Key (optional)", zh: "NASA API 密钥（可选）",
      pt: "Chave API da NASA (opcional)", es: "Clave API de NASA (opcional)",
      ko: "NASA API 키 (선택)", fr: "Clé API NASA (optionnel)", de: "NASA API-Schlüssel (optional)",
      ja: "NASA APIキー（任意）", ar: "مفتاح NASA API (اختياري)", ru: "Ключ API NASA (необязательно)" },
    "settings.apikey.hint": { en: "Leave blank to use the shared DEMO_KEY. Get a free key at api.nasa.gov.",
      zh: "留空使用共享的 DEMO_KEY。可在 api.nasa.gov 免费获取密钥。",
      pt: "Deixe vazio para usar o DEMO_KEY partilhado. Obtenha uma chave gratuita em api.nasa.gov.",
      es: "Déjalo vacío para usar DEMO_KEY. Obtén una clave gratis en api.nasa.gov.",
      ko: "공유 DEMO_KEY를 쓰려면 비워두세요. api.nasa.gov에서 무료 키를 받으세요.",
      fr: "Laissez vide pour DEMO_KEY. Clé gratuite sur api.nasa.gov.",
      de: "Leer lassen für DEMO_KEY. Kostenloser Schlüssel auf api.nasa.gov.",
      ja: "空欄でDEMO_KEYを使用。api.nasa.govで無料キーを取得。",
      ar: "اتركه فارغًا لاستخدام DEMO_KEY. احصل على مفتاح مجاني من api.nasa.gov.",
      ru: "Пусто = DEMO_KEY. Бесплатный ключ на api.nasa.gov." },
    "settings.cache": { en: "Clear cache", zh: "清除缓存", pt: "Limpar cache",
      es: "Borrar caché", ko: "캐시 삭제", fr: "Vider le cache", de: "Cache leeren",
      ja: "キャッシュをクリア", ar: "مسح الذاكرة المؤقتة", ru: "Очистить кэш" },
    "settings.lang": { en: "Language", zh: "语言", pt: "Idioma", es: "Idioma", ko: "언어",
      fr: "Langue", de: "Sprache", ja: "言語", ar: "اللغة", ru: "Язык" },

    "status.live": { en: "LIVE", zh: "实时", pt: "AO VIVO", es: "EN VIVO", ko: "실시간",
      fr: "EN DIRECT", de: "LIVE", ja: "ライブ", ar: "مباشر", ru: "ЖИВОЙ" },
    "status.sample": { en: "SAMPLE", zh: "样本", pt: "AMOSTRA", es: "MUESTRA", ko: "샘플",
      fr: "ÉCHANTILLON", de: "BEISPIEL", ja: "サンプル", ar: "عينة", ru: "ОБРАЗЕЦ" },
    "status.cached": { en: "cached", zh: "缓存", pt: "em cache", es: "en caché", ko: "캐시",
      fr: "en cache", de: "zwischengespeichert", ja: "キャッシュ", ar: "مخزن", ru: "кэш" },

    "panel.loadmore": { en: "Load more", zh: "加载更多", pt: "Carregar mais",
      es: "Cargar más", ko: "더 보기", fr: "Charger plus", de: "Mehr laden",
      ja: "もっと読み込む", ar: "تحميل المزيد", ru: "Загрузить ещё" },
    "panel.hazard": { en: "Potentially Hazardous", zh: "潜在危险", pt: "Potencialmente Perigoso",
      es: "Potencialmente Peligroso", ko: "잠재적 위험", fr: "Potentiellement Dangereux",
      de: "Potenziell Gefährlich", ja: "潜在的に危険", ar: "خطر محتمل", ru: "Потенциально опасен" },
    "panel.nohazard": { en: "Not hazardous", zh: "无危险", pt: "Sem perigo", es: "Sin peligro",
      ko: "위험 없음", fr: "Sans danger", de: "Ungefährlich", ja: "危険なし", ar: "غير خطر", ru: "Не опасен" },

    "footer.disclaimer": {
      en: "Built on NASA's open APIs. Data © NASA. For exploration and education.",
      zh: "基于 NASA 开放 API 构建。数据版权归 NASA。用于探索与教育。",
      pt: "Construído sobre APIs abertas da NASA. Dados © NASA. Para exploração e educação.",
      es: "Construido sobre APIs abiertas de la NASA. Datos © NASA. Para exploración y educación.",
      ko: "NASA 공개 API 기반. 데이터 © NASA. 탐험과 교육을 위해.",
      fr: "Construit sur les API ouvertes de la NASA. Données © NASA. Pour l'exploration et l'éducation.",
      de: "Basiert auf offenen NASA-APIs. Daten © NASA. Für Erkundung und Bildung.",
      ja: "NASAのオープンAPIに基づく構築。データ © NASA。探検と教育のために。",
      ar: "مبني على واجهات الناسا المفتوحة. البيانات © الناسا. للاستكشاف والتعليم.",
      ru: "На основе открытых API NASA. Данные © NASA. Для исследований и образования." }
  };

  function get() {
    var stored = localStorage.getItem("cosmos.lang");
    return (stored && langs[stored]) ? stored : "en";
  }

  function set(code) {
    if (!langs[code]) code = "en";
    localStorage.setItem("cosmos.lang", code);
    document.documentElement.lang = code;
    document.documentElement.dir = rtl[code] ? "rtl" : "ltr";
    global.dispatchEvent(new CustomEvent("langchange", { detail: code }));
    apply(document);
  }

  function t(key, vars) {
    var lang = get();
    var entry = STRINGS[key];
    if (!entry) return key;
    var s = entry[lang] || entry.en || key;
    if (vars) {
      Object.keys(vars).forEach(function (k) {
        s = s.split("{" + k + "}").join(vars[k]);
      });
    }
    return s;
  }

  function apply(root) {
    root = root || document;
    var nodes = root.querySelectorAll("[data-i18n]");
    nodes.forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      var v = el.getAttribute("data-i18n-vars");
      el.textContent = t(key, v ? JSON.parse(v) : null);
    });
    var attrNodes = root.querySelectorAll("[data-i18n-attr]");
    attrNodes.forEach(function (el) {
      // format: "attr:key,attr2:key2"
      el.getAttribute("data-i18n-attr").split(",").forEach(function (pair) {
        var p = pair.split(":");
        el.setAttribute(p[0].trim(), t(p[1].trim()));
      });
    });
  }

  global.I18n = { langs: langs, rtl: rtl, get: get, set: set, t: t, apply: apply };
  // apply saved language + dir on load
  set(get());
})(window);
