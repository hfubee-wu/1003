/*
  理賠文件導航：主程式
  整體流程：讀取 js/data.js 的內容 → 依網址（#/medical 這種）顯示首頁或某個類型的清單 →
  勾選的進度存在這台裝置的瀏覽器（localStorage），不會上傳到任何地方。
*/
(() => {
  'use strict';

  const CFG = Object.assign(
    { siteName: '理賠文件導航', advisorName: '', line: '', email: '', phone: '' },
    window.SITE_CONFIG || {}
  );
  const DATA = window.CLAIM_DATA;
  const app = document.getElementById('app');

  if (!DATA || !Array.isArray(DATA.types)) {
    app.prepend(Object.assign(document.createElement('p'), {
      className: 'noscript',
      textContent: '內容資料載入失敗，請確認 js/data.js 有一起上傳，且沒有被改壞。'
    }));
    return;
  }

  const TYPES = DATA.types;
  const viewHome = document.getElementById('view-home');
  const viewType = document.getElementById('view-type');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const HOME_TITLE = document.title;

  let current = null;     // 目前顯示的類型（首頁時為 null）
  let firstRoute = true;

  /* ========== 小工具 ========== */
  // 建立網頁元素。文字一律用 textContent 放入，避免被塞入程式碼
  function el(tag, attrs, ...kids) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v == null || v === false) continue;
        node.setAttribute(k, v === true ? '' : v);
      }
    }
    for (const kid of kids.flat()) {
      if (kid == null || kid === false) continue;
      node.append(kid);
    }
    return node;
  }

  const countDocs = (type) => type.groups.reduce((n, g) => n + g.docs.length, 0);
  const isSituation = (g) => g.kind === 'situation';
  const kindClass = (k) => ({ 正本: 'k-orig', 影本: 'k-copy', 表單: 'k-form', 照片: 'k-photo' }[k] || 'k-other');
  const typeStyle = (t) => `--type:${t.color};--type-ink:${t.ink};--type-soft:${t.soft}`;

  /* ========== 儲存勾選進度（存不了也不影響使用） ========== */
  const STORE_KEY = 'claimGuide.v1';
  let store = loadStore();

  function loadStore() {
    const empty = { docs: {}, groups: {} };
    try {
      const o = JSON.parse(localStorage.getItem(STORE_KEY) || 'null');
      if (!o || typeof o !== 'object') return empty;
      const clean = (src) => {
        const out = {};
        for (const [k, v] of Object.entries(src || {})) {
          if (Array.isArray(v)) out[k] = v.filter((x) => typeof x === 'string');
        }
        return out;
      };
      return { docs: clean(o.docs), groups: clean(o.groups) };
    } catch (e) {
      return empty;
    }
  }
  function saveStore() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(store)); } catch (e) { /* 無痕模式等情況，略過 */ }
  }
  function setIn(bucket, typeId, id, on) {
    const list = new Set(bucket[typeId] || []);
    if (on) list.add(id); else list.delete(id);
    bucket[typeId] = [...list];
  }

  /* ========== 聯絡區塊 ========== */
  function contactBlock() {
    const line = String(CFG.line || '').trim();
    const email = String(CFG.email || '').trim();
    const phone = String(CFG.phone || '').trim();
    const tel = phone.replace(/[^\d+]/g, '');
    const buttons = [];
    const printLines = [];

    if (/^https:\/\//i.test(line)) {
      buttons.push(el('a', { class: 'btn', href: line, target: '_blank', rel: 'noopener noreferrer' }, '用 LINE 聯絡'));
      printLines.push('LINE：' + line);
    }
    if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      buttons.push(el('a', { class: 'btn btn-ghost', href: 'mailto:' + email }, '寄 Email'));
      printLines.push('Email：' + email);
    }
    if (tel.length >= 6) {
      buttons.push(el('a', { class: 'btn btn-ghost', href: 'tel:' + tel }, '撥打電話'));
      printLines.push('電話：' + phone);
    }
    if (!buttons.length) return null;

    const name = String(CFG.advisorName || '').trim();
    return [
      el('p', { class: 'eyebrow' }, 'Contact'),
      el('h2', null, '理賠遇到問題，一起看看'),
      el('p', null, name
        ? `不確定該備哪些文件、或對保單條款有疑問，歡迎聯絡${name}。`
        : '不確定該備哪些文件、或對保單條款有疑問，歡迎聯絡我。'),
      el('div', { class: 'cta-buttons' }, buttons)
    ];
  }

  /* ========== 首頁 ========== */
  function renderHome() {
    document.getElementById('brand-name').textContent = CFG.siteName;
    document.getElementById('site-name-foot').textContent = CFG.siteName;
    document.getElementById('updated').textContent = DATA.updated || '';

    document.getElementById('type-grid').replaceChildren(...TYPES.map((t) =>
      el('a', { class: 'type-card', href: `#/${t.id}`, style: typeStyle(t) },
        el('div', { class: 'type-card-top' },
          el('img', { src: t.icon, alt: '', width: 64, height: 64 }),
          el('div', null,
            el('p', { class: 'eyebrow' }, t.en || ''),
            el('h3', null, t.name))),
        el('p', { class: 'card-rule' }, `共 ${countDocs(t)} 份文件`),
        el('p', { class: 'blurb' }, t.blurb),
        el('span', { class: 'btn' }, '查看文件清單'))
    ));

    document.getElementById('steps-list').replaceChildren(...(DATA.steps || []).map((s) =>
      el('li', null, el('h3', null, s.title), el('p', null, s.text))
    ));

    document.getElementById('faq-list').replaceChildren(...(DATA.faq || []).map(faqItem));

    const slot = document.getElementById('contact');
    const c = contactBlock();
    if (c) slot.replaceChildren(...c); else slot.hidden = true;
  }

  function faqItem(f) {
    return el('details', null,
      el('summary', null, f.q),
      el('div', { class: 'faq-a' }, el('p', null, f.a)));
  }

  /* ========== 類型頁 ========== */
  function docItem(type, d, checked) {
    const meta = [['去哪裡', d.where], ['費用', d.cost], ['時間', d.time]].filter(([, v]) => v);
    const more = (meta.length || d.tip)
      ? el('details', { class: 'doc-more' },
          el('summary', null, '怎麼取得、要注意什麼'),
          meta.length ? el('dl', { class: 'doc-meta' }, meta.flatMap(([k, v]) => [el('dt', null, k), el('dd', null, v)])) : null,
          d.tip ? el('p', { class: 'doc-tip' }, el('span', { class: 'tag' }, '小提醒'), d.tip) : null)
      : null;

    return el('li', { class: 'doc' + (checked ? ' is-done' : '') },
      el('label', { class: 'check' },
        el('input', { type: 'checkbox', class: 'doc-check', 'data-doc': d.id, checked }),
        el('span', { class: 'box', 'aria-hidden': 'true' }),
        el('span', { class: 'doc-name' }, d.name, d.kind ? el('span', { class: 'kind ' + kindClass(d.kind) }, d.kind) : null)),
      el('p', { class: 'doc-what' }, d.what),
      more);
  }

  function groupBlock(type, g, checkedDocs, activeGroups) {
    const situation = isSituation(g);
    const active = !situation || activeGroups.has(g.id);
    const bodyId = `gb-${type.id}-${g.id}`;

    const body = el('div', { class: 'group-body', id: bodyId, hidden: !active },
      el('ul', { class: 'docs' }, g.docs.map((d) => docItem(type, d, checkedDocs.has(d.id)))));

    const head = situation
      ? el('label', { class: 'group-head toggle check' },
          el('input', { type: 'checkbox', class: 'group-toggle', 'data-group': g.id, 'aria-controls': bodyId, checked: active }),
          el('span', { class: 'box', 'aria-hidden': 'true' }),
          el('span', { class: 'group-text' },
            el('span', { class: 'group-title' }, g.title),
            g.desc ? el('small', null, g.desc) : null))
      : el('div', { class: 'group-head' },
          el('h3', null, g.title),
          g.desc ? el('p', { class: 'group-desc' }, g.desc) : null);

    return el('section', { class: 'group ' + (situation ? 'situation' : 'base') + (active ? '' : ' is-off'), 'data-group': g.id },
      head, body);
  }

  function renderType(type) {
    const checkedDocs = new Set(store.docs[type.id] || []);
    const activeGroups = new Set(store.groups[type.id] || []);
    const today = new Date().toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric' });
    const others = TYPES.filter((t) => t.id !== type.id);
    const hasSituations = type.groups.some(isSituation);

    viewType.setAttribute('style', typeStyle(type));
    viewType.replaceChildren(el('div', { class: 'container' },
      el('p', { class: 'print-only print-head' }, `${CFG.siteName}｜${type.name}理賠文件清單｜列印日期：${today}`),
      el('p', { class: 'crumb no-print' }, el('a', { href: '#/' }, '← 回到理賠類型')),

      el('header', { class: 'type-head' },
        el('img', { src: type.icon, alt: '', width: 88, height: 88 }),
        el('div', null,
          el('p', { class: 'eyebrow' }, type.en || ''),
          el('h1', { id: 'type-title', tabindex: '-1' }, type.name)),
        el('p', { class: 'lead' }, type.intro)),

      (type.firstSteps && type.firstSteps.length)
        ? el('section', { class: 'callout', 'aria-labelledby': 'first-title' },
            el('h2', { id: 'first-title' }, '事情發生後，先做這幾件事'),
            el('ol', null, type.firstSteps.map((s) => el('li', null, el('span', null, s)))))
        : null,

      el('section', { class: 'checklist', 'aria-labelledby': 'list-title' },
        el('div', { class: 'checklist-head' },
          el('p', { class: 'eyebrow' }, 'Checklist'),
          el('h2', { id: 'list-title' }, '要準備的文件'),
          el('p', { class: 'how-to no-print' }, hasSituations
            ? '先看「基本文件」；再勾選下面符合你情況的項目，對應的文件就會加進清單。準備好一份就勾一份，進度會自動記住。'
            : '準備好一份就勾一份，進度會自動記住。')),
        el('div', { class: 'progress', id: 'progress' },
          el('div', { class: 'progress-row' },
            el('p', { class: 'progress-text', id: 'progress-text', 'aria-live': 'polite' }),
            el('p', { class: 'progress-hint', id: 'progress-hint' })),
          el('div', { class: 'bar', id: 'progress-bar', role: 'progressbar', 'aria-label': '文件備齊進度', 'aria-valuemin': '0' }, el('i', { id: 'progress-fill' }))),
        type.groups.map((g) => groupBlock(type, g, checkedDocs, activeGroups)),
        el('div', { class: 'actions no-print' },
          el('button', { type: 'button', class: 'btn', id: 'print-btn' }, '列印／存成 PDF'),
          el('button', { type: 'button', class: 'btn btn-ghost', id: 'reset-btn' }, '清除這一頁的勾選'))),

      (type.tips && type.tips.length)
        ? el('section', { class: 'type-block', 'aria-labelledby': 'tips-title' },
            el('p', { class: 'eyebrow' }, 'Tips'),
            el('h2', { id: 'tips-title' }, '理賠小提醒'),
            el('ul', { class: 'tip-list' }, type.tips.map((t) => el('li', null, t))))
        : null,

      (type.faq && type.faq.length)
        ? el('section', { class: 'type-block faq-block no-print', 'aria-labelledby': 'tfaq-title' },
            el('p', { class: 'eyebrow' }, 'Q&A'),
            el('h2', { id: 'tfaq-title' }, '常見問題'),
            el('div', { class: 'faq' }, type.faq.map(faqItem)))
        : null,

      el('section', { class: 'type-block more-block no-print', 'aria-labelledby': 'more-title' },
        el('p', { class: 'eyebrow' }, 'More'),
        el('h2', { id: 'more-title' }, '看看其他理賠類型'),
        el('ul', { class: 'type-pills' }, others.map((t) =>
          el('li', null, el('a', { class: 'pill', href: `#/${t.id}` },
            el('img', { src: t.icon, alt: '', width: 40, height: 40 }), t.name)))))
    ));

    updateProgress();
  }

  function updateProgress() {
    if (!current) return;
    const checkedDocs = new Set(store.docs[current.id] || []);
    const activeGroups = new Set(store.groups[current.id] || []);
    let total = 0;
    let done = 0;
    for (const g of current.groups) {
      if (isSituation(g) && !activeGroups.has(g.id)) continue;
      for (const d of g.docs) {
        total += 1;
        if (checkedDocs.has(d.id)) done += 1;
      }
    }
    const complete = total > 0 && done === total;
    const text = document.getElementById('progress-text');
    text.replaceChildren(
      complete ? '文件都備齊了' : '已備齊',
      complete ? '' : el('span', { class: 'num' }, `${done}／${total}`),
      complete ? '' : '份文件');
    const anyGroupOn = current.groups.some((g) => isSituation(g) && activeGroups.has(g.id));
    document.getElementById('progress-hint').textContent = complete
      ? '可以準備送件了。'
      : (anyGroupOn || !current.groups.some(isSituation) ? '' : '勾選符合你情況的項目，會加入更多文件。');
    document.getElementById('progress').classList.toggle('is-complete', complete);
    document.getElementById('progress-fill').style.width = (total ? (done / total) * 100 : 0).toFixed(1) + '%';
    const bar = document.getElementById('progress-bar');
    bar.setAttribute('aria-valuemax', String(total));
    bar.setAttribute('aria-valuenow', String(done));
  }

  /* ========== 事件：勾選、清除、列印 ========== */
  viewType.addEventListener('change', (e) => {
    const t = e.target;
    if (!(t instanceof HTMLInputElement) || !current) return;
    if (t.classList.contains('doc-check')) {
      setIn(store.docs, current.id, t.dataset.doc, t.checked);
      t.closest('.doc').classList.toggle('is-done', t.checked);
    } else if (t.classList.contains('group-toggle')) {
      setIn(store.groups, current.id, t.dataset.group, t.checked);
      const group = t.closest('.group');
      group.classList.toggle('is-off', !t.checked);
      group.querySelector('.group-body').hidden = !t.checked;
    } else {
      return;
    }
    saveStore();
    updateProgress();
  });

  viewType.addEventListener('click', (e) => {
    if (!current) return;
    if (e.target.closest('#print-btn')) {
      window.print();
    } else if (e.target.closest('#reset-btn')) {
      if (!window.confirm('要清除這一頁所有的勾選嗎？')) return;
      delete store.docs[current.id];
      delete store.groups[current.id];
      saveStore();
      const y = window.scrollY;
      renderType(current);
      window.scrollTo(0, y);
    }
  });

  // 列印時把「怎麼取得」全部展開，列印完再還原
  let openedForPrint = [];
  window.addEventListener('beforeprint', () => {
    openedForPrint = [...viewType.querySelectorAll('details:not([open])')];
    openedForPrint.forEach((d) => { d.open = true; });
  });
  window.addEventListener('afterprint', () => {
    openedForPrint.forEach((d) => { d.open = false; });
    openedForPrint = [];
  });

  /* ========== 網址切換頁面 ========== */
  function scrollToTop() { window.scrollTo(0, 0); }

  function showType(type) {
    current = type;
    renderType(type);
    viewHome.hidden = true;
    viewType.hidden = false;
    document.title = `${type.name}理賠文件清單｜${CFG.siteName}`;
    scrollToTop();
    if (!firstRoute) document.getElementById('type-title').focus({ preventScroll: true });
  }

  function showHome(hash) {
    const wasType = current !== null;
    current = null;
    viewType.hidden = true;
    viewHome.hidden = false;
    document.title = HOME_TITLE;

    let target = null;
    const id = hash.length > 1 && hash !== '#/' ? decodeURIComponent(hash.slice(1)) : '';
    if (id) target = document.getElementById(id);

    if (target && viewHome.contains(target)) {
      target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    } else if (wasType) {
      // 從類型頁回來：停在「理賠類型」，方便接著選別的
      const types = document.getElementById('types');
      types.scrollIntoView({ block: 'start' });
      document.getElementById('types-title').focus({ preventScroll: true });
    } else if (!firstRoute) {
      scrollToTop();
    }
  }

  function route() {
    const hash = location.hash;

    // 頁尾（聯絡）在每個頁面都有，點到時不切換頁面，只捲動過去
    if (hash.length > 1 && !hash.startsWith('#/')) {
      let footTarget = null;
      try { footTarget = document.getElementById(decodeURIComponent(hash.slice(1))); } catch (e) { /* 網址格式不合，略過 */ }
      if (footTarget && footTarget.closest('.site-footer')) {
        footTarget.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
        return;
      }
    }

    const m = /^#\/([\w-]+)$/.exec(hash);
    const type = m && TYPES.find((t) => t.id === m[1]);
    if (type) showType(type); else showHome(hash);
    firstRoute = false;
  }

  /* ========== 其他：跳到主要內容、回到最上方 ========== */
  document.getElementById('skip-link').addEventListener('click', (e) => {
    e.preventDefault();
    app.focus();
  });
  const pageTop = document.getElementById('page-top');
  pageTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
  });
  window.addEventListener('scroll', () => {
    pageTop.classList.toggle('is-visible', window.scrollY > 480);
  }, { passive: true });

  /* ========== 啟動 ========== */
  renderHome();
  window.addEventListener('hashchange', route);
  route();
})();
