(() => {
  "use strict";

  const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  const params = new URLSearchParams(window.location.search);
  const strings = {
    ru: {
      loading: "Загружаю варианты…",
      updating: "Обновляю предпросмотр…",
      select: "Выбери вариант — превью обновится сразу.",
      applyHint: "Выбери вариант и нажми «Применить в боте».",
      applying: "Применяю настройки…",
      done: "Готово. Возвращаюсь в бота…",
      applyFailed: "Не удалось применить настройки. Попробуй ещё раз.",
      sendFailed: "Не удалось отправить настройки. Попробуй ещё раз.",
      openTelegram: "Открой редактор через Telegram, чтобы применить настройки.",
      catalogFailed: "Не удалось загрузить каталог. Обнови страницу.",
      empty: "Ничего не найдено",
      all: "Все",
      close: "Закрыть",
      sections: "Разделы",
      previewAlt: "Предпросмотр QR",
      previewTitle: "Так будет выглядеть QR",
      apply: "Применить в боте",
      tabs: {
        shapes: "Формы",
        modules: "Узоры",
        eyes: "Глаза",
        palettes: "Палитры",
        presets: "Пресеты",
        sizes: "Размер"
      }
    },
    en: {
      loading: "Loading options…",
      updating: "Updating preview…",
      select: "Choose an option — the preview updates instantly.",
      applyHint: "Choose an option and tap “Apply in bot”.",
      applying: "Applying settings…",
      done: "Done. Returning to the bot…",
      applyFailed: "Couldn't apply the settings. Try again.",
      sendFailed: "Couldn't send the settings. Try again.",
      openTelegram: "Open the editor through Telegram to apply the settings.",
      catalogFailed: "Couldn't load the catalog. Refresh the page.",
      empty: "Nothing found",
      all: "All",
      close: "Close",
      sections: "Sections",
      previewAlt: "QR preview",
      previewTitle: "This is how the QR will look",
      apply: "Apply in bot",
      tabs: {
        shapes: "Shapes",
        modules: "Patterns",
        eyes: "Eyes",
        palettes: "Palettes",
        presets: "Presets",
        sizes: "Size"
      }
    }
  };

  function storedLang() {
    try {
      return window.localStorage.getItem("qrstudio.lang") || "";
    } catch (error) {
      return "";
    }
  }

  function resolveLang() {
    const telegramLang = tg && tg.initDataUnsafe && tg.initDataUnsafe.user
      ? tg.initDataUnsafe.user.language_code
      : "";
    const raw = String(params.get("lang") || storedLang() || telegramLang || navigator.language || "").toLowerCase().replace(/_/g, "-");
    if (!raw) return "ru";
    if (raw.startsWith("ru") || raw.startsWith("uk") || raw.startsWith("be") || raw.startsWith("kk")) return "ru";
    if (raw.startsWith("en")) return "en";
    return "en";
  }

  let lang = resolveLang();
  let s = strings[lang];
  document.documentElement.lang = lang;

  const state = {
    shape: params.get("shape") || "square",
    module_style: params.get("module") || params.get("module_style") || "dot",
    eye_style: params.get("eye") || params.get("eye_style") || "circle",
    palette: params.get("palette") || "blue",
    size: Number(params.get("size") || 1024),
    preset: null
  };
  const fields = { shapes: "shape", modules: "module_style", eyes: "eye_style", palettes: "palette" };
  const tabKeys = ["shapes", "modules", "eyes", "palettes", "presets", "sizes"];
  const el = {
    status: document.getElementById("status"),
    preview: document.getElementById("preview"),
    previewTitle: document.getElementById("preview-title"),
    summary: document.getElementById("summary"),
    tabs: document.getElementById("tabs"),
    subcats: document.getElementById("subcats"),
    grid: document.getElementById("grid"),
    apply: document.getElementById("apply"),
    close: document.getElementById("close"),
    lang: document.getElementById("lang")
  };
  let catalog = null;
  let catalogRequest = 0;
  let activeTab = "shapes";
  let activeCategory = "all";
  let previewTimer = 0;
  const nameMaps = { shapes: {}, modules: {}, eyes: {}, palettes: {}, presets: {} };

  function applyTheme() {
    if (!tg) return;
    const p = tg.themeParams || {};
    const root = document.documentElement;
    const map = {
      bg_color: "--bg",
      secondary_bg_color: "--surface-2",
      text_color: "--text",
      hint_color: "--muted",
      button_color: "--accent",
      section_separator_color: "--line"
    };
    Object.keys(map).forEach((key) => {
      if (p[key]) root.style.setProperty(map[key], p[key]);
    });
    if (p.secondary_bg_color) root.style.setProperty("--surface", p.secondary_bg_color);
  }

  function escapeText(value) {
    return String(value == null ? "" : value);
  }

  function allShapes() {
    return catalog.shapes.flatMap((group) => group.items);
  }

  function currentItems() {
    if (activeTab === "shapes") {
      if (activeCategory === "all") return allShapes();
      const group = catalog.shapes.find((item) => item.key === activeCategory);
      return group ? group.items : allShapes();
    }
    if (activeTab === "sizes") {
      return catalog.sizes.map((size) => ({ key: String(size), name: size + " px" }));
    }
    return catalog[activeTab] || [];
  }

  function selectedKey() {
    if (activeTab === "sizes") return String(state.size);
    if (activeTab === "presets") return state.preset;
    return state[fields[activeTab]];
  }

  function buildTabs() {
    el.tabs.replaceChildren();
    tabKeys.forEach((key) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "tab" + (key === activeTab ? " active" : "");
      button.textContent = s.tabs[key];
      button.addEventListener("click", () => {
        activeTab = key;
        buildTabs();
        buildSubcats();
        renderGrid();
      });
      el.tabs.appendChild(button);
    });
  }

  function buildSubcats() {
    el.subcats.replaceChildren();
    el.subcats.hidden = activeTab !== "shapes";
    if (activeTab !== "shapes") return;
    const groups = [{ key: "all", name: s.all }].concat(catalog.shapes.map(({ key, name }) => ({ key, name })));
    groups.forEach((group) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "subcat" + (group.key === activeCategory ? " active" : "");
      button.textContent = group.name;
      button.addEventListener("click", () => {
        activeCategory = group.key;
        buildSubcats();
        renderGrid();
      });
      el.subcats.appendChild(button);
    });
  }

  function makeCard(item, selected, kind) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "card" + (selected ? " selected" : "");
    card.setAttribute("aria-pressed", selected ? "true" : "false");
    if (kind === "sizes") {
      card.classList.add("size-card");
      const value = document.createElement("span");
      value.className = "size";
      value.textContent = item.key;
      const unit = document.createElement("span");
      unit.className = "size-unit";
      unit.textContent = "px";
      card.append(value, unit);
    } else {
      const thumb = document.createElement("span");
      thumb.className = "thumb";
      const image = document.createElement("img");
      image.src = item.thumb;
      image.alt = item.name;
      image.loading = "lazy";
      image.decoding = "async";
      thumb.appendChild(image);
      const caption = document.createElement("span");
      caption.className = "caption";
      caption.textContent = item.name;
      card.append(thumb, caption);
    }
    const check = document.createElement("span");
    check.className = "check";
    check.textContent = "✓";
    card.appendChild(check);
    card.addEventListener("click", () => {
      if (kind === "sizes") {
        state.size = Number(item.key);
      } else if (kind === "presets") {
        state.shape = item.shape;
        state.module_style = item.module_style;
        state.eye_style = item.eye_style;
        state.palette = item.palette;
        state.preset = item.key;
      } else {
        state[fields[kind]] = item.key;
        state.preset = null;
      }
      updateSummary();
      updatePreview();
      renderGrid();
    });
    return card;
  }

  function renderGrid() {
    const selected = selectedKey();
    const items = currentItems();
    el.grid.replaceChildren();
    items.forEach((item) => {
      el.grid.appendChild(makeCard(item, item.key === selected, activeTab));
    });
    if (!items.length) {
      const empty = document.createElement("p");
      empty.className = "empty";
      empty.textContent = s.empty;
      el.grid.appendChild(empty);
    }
  }

  function updateSummary() {
    const shape = nameMaps.shapes[state.shape] || state.shape;
    const module = nameMaps.modules[state.module_style] || state.module_style;
    const eye = nameMaps.eyes[state.eye_style] || state.eye_style;
    const palette = nameMaps.palettes[state.palette] || state.palette;
    el.summary.textContent = shape + " · " + module + " · " + eye + " · " + palette + " · " + state.size + " px";
  }

  function updatePreview() {
    window.clearTimeout(previewTimer);
    el.status.textContent = s.updating;
    previewTimer = window.setTimeout(() => {
      const query = new URLSearchParams({
        shape: state.shape,
        module: state.module_style,
        eye: state.eye_style,
        palette: state.palette,
        size: "400"
      });
      el.preview.src = "/app/preview.png?" + query.toString();
    }, 120);
  }

  function normalizeState() {
    const shapes = new Set(allShapes().map((item) => item.key));
    const modules = new Set(catalog.modules.map((item) => item.key));
    const eyes = new Set(catalog.eyes.map((item) => item.key));
    const palettes = new Set(catalog.palettes.map((item) => item.key));
    const sizes = new Set(catalog.sizes.map(String));
    if (!shapes.has(state.shape)) state.shape = "square";
    if (!modules.has(state.module_style)) state.module_style = "dot";
    if (!eyes.has(state.eye_style)) state.eye_style = "circle";
    if (!palettes.has(state.palette)) state.palette = "blue";
    if (!sizes.has(String(state.size))) state.size = 1024;
  }

  function fillNames() {
    allShapes().forEach((item) => { nameMaps.shapes[item.key] = item.name; });
    catalog.modules.forEach((item) => { nameMaps.modules[item.key] = item.name; });
    catalog.eyes.forEach((item) => { nameMaps.eyes[item.key] = item.name; });
    catalog.palettes.forEach((item) => { nameMaps.palettes[item.key] = item.name; });
    catalog.presets.forEach((item) => { nameMaps.presets[item.key] = item.name; });
  }

  function applyStrings() {
    el.apply.textContent = s.apply;
    el.preview.alt = s.previewAlt;
    el.close.setAttribute("aria-label", s.close);
    el.tabs.setAttribute("aria-label", s.sections);
    if (el.previewTitle) el.previewTitle.textContent = s.previewTitle;
    if (el.lang) {
      el.lang.textContent = lang === "ru" ? "EN" : "RU";
      el.lang.setAttribute("aria-label", lang === "ru" ? "Switch to English" : "Переключить на русский");
      el.lang.title = lang === "ru" ? "Switch to English" : "Переключить на русский";
    }
  }

  async function loadCatalog() {
    const request = ++catalogRequest;
    el.status.textContent = s.loading;
    try {
      const response = await fetch("/app/catalog.json?lang=" + encodeURIComponent(lang), { cache: "no-store" });
      if (!response.ok) throw new Error("catalog");
      const nextCatalog = await response.json();
      if (request !== catalogRequest) return;
      catalog = nextCatalog;
      normalizeState();
      fillNames();
      buildTabs();
      buildSubcats();
      updateSummary();
      renderGrid();
      updatePreview();
      el.status.textContent = s.select;
    } catch (error) {
      if (request === catalogRequest) el.status.textContent = s.catalogFailed;
    }
  }

  function setLanguage(next) {
    if (!strings[next] || next === lang) return;
    lang = next;
    s = strings[lang];
    document.documentElement.lang = lang;
    try {
      window.localStorage.setItem("qrstudio.lang", lang);
    } catch (error) {}
    try {
      const url = new URL(window.location.href);
      url.searchParams.set("lang", lang);
      window.history.replaceState(null, "", url);
    } catch (error) {}
    applyStrings();
    if (catalog) {
      buildTabs();
      buildSubcats();
      updateSummary();
      renderGrid();
    }
    loadCatalog();
  }

  async function applySelection() {
    const payload = {
      shape: state.shape,
      module_style: state.module_style,
      eye_style: state.eye_style,
      palette: state.palette,
      size: state.size,
      lang: lang
    };
    if (tg && tg.initData) {
      el.status.textContent = s.applying;
      try {
        const response = await fetch("/app/apply", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ init_data: tg.initData, data: payload })
        });
        if (!response.ok) throw new Error("apply");
        el.status.textContent = s.done;
        window.setTimeout(() => tg.close(), 180);
      } catch (error) {
        el.status.textContent = s.applyFailed;
      }
      return;
    }
    if (!tg || typeof tg.sendData !== "function") {
      el.status.textContent = s.openTelegram;
      return;
    }
    try {
      tg.sendData(JSON.stringify(payload));
      el.status.textContent = s.done;
      window.setTimeout(() => tg.close(), 180);
    } catch (error) {
      el.status.textContent = s.sendFailed;
    }
  }

  async function init() {
    applyStrings();
    if (tg) {
      tg.ready();
      tg.expand();
      applyTheme();
      if (typeof tg.onEvent === "function") tg.onEvent("themeChanged", applyTheme);
      if (typeof tg.setHeaderColor === "function") tg.setHeaderColor("secondary_bg_color");
    }
    el.apply.addEventListener("click", applySelection);
    if (el.lang) el.lang.addEventListener("click", () => setLanguage(lang === "ru" ? "en" : "ru"));
    el.close.addEventListener("click", () => {
      if (tg && typeof tg.close === "function") tg.close();
      else window.close();
    });
    el.preview.addEventListener("load", () => {
      el.status.textContent = s.applyHint;
    });
    await loadCatalog();
  }

  init();
})();
