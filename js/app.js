/*
  保障缺口試算器：主程式
  整體流程：讀取表單 → 檢查數字 → 計算四種保障的「需要／已有／缺口」 → 畫出報告
  金額單位除了標明「元／日」之外，一律是「萬元」。
*/
(() => {
  'use strict';

  const CFG = Object.assign(
    { siteName: '保障缺口試算器', advisorName: '', line: '', email: '', phone: '' },
    window.SITE_CONFIG || {}
  );

  const form = document.getElementById('calc-form');
  const report = document.getElementById('report');
  const formError = document.getElementById('form-error');
  const resetBtn = document.getElementById('reset-btn');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ========== 欄位規則：名稱、是否必填、可填範圍 ========== */
  const BIG = 100000; // 金額（萬元）上限，避免亂填
  const FIELDS = {
    age:           { label: '現在年齡',               required: true, min: 18, max: 80, integer: true },
    retireAge:     { label: '預計工作到幾歲',         min: 40, max: 90, integer: true, fallback: 65 },
    monthlyIncome: { label: '平均每月收入',           required: true, max: 1000 },
    familyMonthly: { label: '家人每月基本生活開銷',   required: true, max: 1000 },
    supportYears:  { label: '家人需要被照顧幾年',     max: 80 },
    debt:          { label: '房貸與其他負債餘額',     max: BIG },
    kids:          { label: '需要扶養的子女人數',     max: 10, integer: true },
    eduPerKid:     { label: '每位子女的教育預備金',   max: BIG },
    finalExpense:  { label: '身後費用',               max: BIG },
    savings:       { label: '家人可動用的存款與投資', max: BIG },
    lifeCover:     { label: '目前壽險的身故保額合計', max: BIG },
    hospDays:      { label: '預估住院天數',           max: 365, integer: true },
    roomDiff:      { label: '病房差額（每天）',       max: 1000000 },
    nurse:         { label: '看護費（每天）',         max: 1000000 },
    selfPay:       { label: '自費醫療項目',           max: BIG },
    dailyCover:    { label: '目前每天可領的住院給付', max: 1000000 },
    reimburse:     { label: '目前實支實付的額度',     max: BIG },
    ciTreat:       { label: '自費治療費用',           max: BIG },
    ciMonths:      { label: '休養、無法工作的時間',   max: 600, integer: true },
    ciCover:       { label: '目前重大疾病險的給付',   max: BIG },
    careMonthly:   { label: '每月照護費用',           max: 1000 },
    careYears:     { label: '需要照護幾年',           max: 80 },
    workLossYears: { label: '失能後無法工作的年數',   max: 80 },
    disLump:       { label: '失能／長照險的一次給付', max: BIG },
    disMonthly:    { label: '失能／長照險的每月給付', max: 1000 }
  };

  /* ========== 小工具 ========== */
  const nf0 = new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 1 });
  const nf2 = new Intl.NumberFormat('zh-TW', { maximumFractionDigits: 2 });

  // 把「萬元」數字轉成好讀的字串（超過一億就改用「億元」）
  function wanParts(n) {
    const v = Math.round(n * 10) / 10;
    if (Math.abs(v) >= 10000) return { num: nf2.format(v / 10000), unit: '億元' };
    return { num: nf1.format(v), unit: '萬元' };
  }
  function wan(n) {
    const p = wanParts(n);
    return p.num + ' ' + p.unit;
  }
  // 方塊裡的大數字：數字一行、單位一行，小螢幕才不會被截斷成兩半
  function statValue(n) {
    const p = wanParts(n);
    return el('b', null, p.num, el('small', null, p.unit));
  }
  const yuan = (n) => nf0.format(n) + ' 元';
  const sum = (rows) => rows.reduce((total, r) => total + r.value, 0);

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

  /* ========== 讀取並檢查表單 ========== */
  function readForm() {
    const values = {};
    const errors = [];
    for (const [id, f] of Object.entries(FIELDS)) {
      const input = document.getElementById(id);
      const min = f.min ?? 0;
      const raw = input.value.trim();
      let val;

      if (input.validity && input.validity.badInput) {
        errors.push({ id, msg: `「${f.label}」請輸入數字` });
        continue;
      }
      if (raw === '') {
        if (f.required) {
          errors.push({ id, msg: `請填寫「${f.label}」` + (min === 0 ? '（沒有的話請填 0）' : '') });
          continue;
        }
        val = f.fallback ?? 0;
      } else {
        val = Number(raw);
        if (!Number.isFinite(val)) {
          errors.push({ id, msg: `「${f.label}」請輸入數字` });
          continue;
        }
        if (val < min || val > f.max) {
          errors.push({ id, msg: `「${f.label}」請填 ${nf0.format(min)} 到 ${nf0.format(f.max)} 之間的數字` });
          continue;
        }
        if (f.integer && !Number.isInteger(val)) {
          errors.push({ id, msg: `「${f.label}」請填整數` });
          continue;
        }
      }
      values[id] = val;
    }
    return { values, errors };
  }

  function setFieldError(input, msg) {
    const field = input.closest('.field');
    let p = field.querySelector('.field-error');
    if (input.dataset.baseDesc === undefined) {
      input.dataset.baseDesc = input.getAttribute('aria-describedby') || '';
    }
    if (!msg) {
      if (p) p.remove();
      input.removeAttribute('aria-invalid');
      if (input.dataset.baseDesc) input.setAttribute('aria-describedby', input.dataset.baseDesc);
      else input.removeAttribute('aria-describedby');
      return;
    }
    if (!p) {
      p = el('p', { class: 'field-error', id: input.id + '-error' });
      field.append(p);
    }
    p.textContent = msg;
    input.setAttribute('aria-invalid', 'true');
    input.setAttribute('aria-describedby', (input.dataset.baseDesc + ' ' + p.id).trim());
  }

  function clearAllErrors() {
    for (const id of Object.keys(FIELDS)) setFieldError(document.getElementById(id), '');
    formError.hidden = true;
    formError.textContent = '';
  }

  /* ========== 計算 ========== */
  function statusOf(pct) {
    if (pct >= 1) return { key: 'ok', text: '保障足夠' };
    if (pct >= 0.7) return { key: 'near', text: '接近足夠' };
    if (pct >= 0.4) return { key: 'low', text: '有缺口' };
    return { key: 'critical', text: '缺口很大' };
  }

  function makeCategory(c) {
    const need = sum(c.needRows);
    const have = sum(c.haveRows);
    let gap = Math.max(0, need - have);
    if (gap < 0.05) gap = 0; // 小於 500 元視為沒有缺口
    const pct = gap === 0 ? 1 : have / need;
    return Object.assign({}, c, { need, have, gap, pct, status: statusOf(pct) });
  }

  function calculate(v) {
    // 失能後少賺的收入，最多只算到退休年齡
    const workYears = Math.min(v.workLossYears, Math.max(0, v.retireAge - v.age));

    // 1. 壽險：家人生活費 + 負債 + 子女教育金 + 身後費用，扣掉現有壽險與存款
    const life = makeCategory({
      key: 'life', short: '壽險', title: '壽險（身故保障）', icon: 'images/icon-life.svg',
      needRows: [
        { label: '家人生活費', note: `${nf1.format(v.familyMonthly)} 萬 × 12 個月 × ${nf1.format(v.supportYears)} 年`, value: v.familyMonthly * 12 * v.supportYears },
        { label: '房貸與其他負債', note: '一次還清', value: v.debt },
        { label: '子女教育金', note: `${v.kids} 位 × ${nf1.format(v.eduPerKid)} 萬`, value: v.kids * v.eduPerKid },
        { label: '身後費用', note: '喪葬及相關雜支', value: v.finalExpense }
      ],
      haveRows: [
        { label: '目前壽險身故保額', value: v.lifeCover },
        { label: '家人可動用的存款與投資', value: v.savings }
      ],
      extra: `對照：常見的「雙十原則」建議壽險保額約為年收入的 10 倍，以你的收入來看約 ${wan(v.monthlyIncome * 12 * 10)}；你目前的壽險保額為 ${wan(v.lifeCover)}。雙十原則只是粗略的經驗法則，上面的算法會更貼近你的家庭狀況。`
    });

    // 2. 醫療：每天花費與自費項目「分開比較」，某一項超出的保障不拿去抵另一項
    const dailyNeed = (v.roomDiff + v.nurse) * v.hospDays / 10000;
    const dailyHaveRaw = v.dailyCover * v.hospDays / 10000;
    const dailyHave = Math.min(dailyHaveRaw, dailyNeed);
    const oopHave = Math.min(v.reimburse, v.selfPay);
    const medical = makeCategory({
      key: 'medical', short: '醫療', title: '醫療（住院與手術）', icon: 'images/icon-medical.svg',
      needRows: [
        { label: '住院期間每日花費', note: `(病房差額 ${yuan(v.roomDiff)} + 看護 ${yuan(v.nurse)}) × ${v.hospDays} 天`, value: dailyNeed },
        { label: '自費醫療項目', note: '自費醫材、藥品、手術方式等', value: v.selfPay }
      ],
      haveRows: [
        { label: '住院每日給付', note: `${yuan(v.dailyCover)} × ${v.hospDays} 天` + (dailyHaveRaw > dailyNeed ? '，超出需求的部分不重複計算' : ''), value: dailyHave },
        { label: '實支實付的雜費與手術額度', note: v.reimburse > v.selfPay ? '超出需求的部分不重複計算' : '', value: oopHave }
      ],
      extra: '醫療這一項是「每天花費」和「自費項目」各自比較：日額給付多了，不會拿去抵自費項目，反之亦然。'
    });

    // 3. 重大疾病：自費治療費 + 休養期間的收入損失
    const critical = makeCategory({
      key: 'critical', short: '重大疾病', title: '重大疾病與癌症', icon: 'images/icon-critical.svg',
      needRows: [
        { label: '自費治療費用', value: v.ciTreat },
        { label: '休養期間的收入損失', note: `${nf1.format(v.monthlyIncome)} 萬 × ${v.ciMonths} 個月`, value: v.monthlyIncome * v.ciMonths }
      ],
      haveRows: [
        { label: '重大疾病／癌症險一次給付', value: v.ciCover }
      ]
    });

    // 4. 失能與長照：照護費用 + 無法工作的收入損失，扣掉一次給付與月給付
    const care = makeCategory({
      key: 'care', short: '失能長照', title: '失能與長期照護', icon: 'images/icon-care.svg',
      needRows: [
        { label: '長期照護費用', note: `${nf1.format(v.careMonthly)} 萬 × 12 個月 × ${nf1.format(v.careYears)} 年`, value: v.careMonthly * 12 * v.careYears },
        {
          label: '無法工作的收入損失',
          note: `${nf1.format(v.monthlyIncome)} 萬 × 12 個月 × ${nf1.format(workYears)} 年` + (workYears < v.workLossYears ? '（最多算到退休年齡）' : ''),
          value: v.monthlyIncome * 12 * workYears
        }
      ],
      haveRows: [
        { label: '失能／長照險一次給付', value: v.disLump },
        { label: '失能／長照險每月給付', note: `${nf1.format(v.disMonthly)} 萬 × 12 個月 × ${nf1.format(v.careYears)} 年`, value: v.disMonthly * 12 * v.careYears }
      ]
    });

    const cats = [life, medical, critical, care];
    cats.forEach((c) => { c.advice = adviceFor(c); });
    return cats;
  }

  // 白話建議：只講方向，不推薦特定商品
  function adviceFor(c) {
    const ok = c.gap === 0;
    const g = wan(c.gap);
    switch (c.key) {
      case 'life':
        return ok
          ? '以你填寫的條件來看，壽險身故保障足以支應家人這段期間的生活、負債與教育支出。之後如果結婚、生子、買房或增貸，建議回來重新試算。'
          : `若發生不幸，家人可能還缺約 ${g}。可以先了解「保額足夠、保費相對低」的定期型保障，把預算放在家人最需要被保護的那段時間。`;
      case 'medical':
        return ok
          ? '住院期間的每日花費與自費項目，目前都有保障可以對應。實支實付的理賠條件與額度各家不同，建議定期檢視保單。'
          : `一次較嚴重的住院，你可能需要自己負擔約 ${g}。可以檢視自己是否同時有「實支實付」與「住院日額」，看看是哪一邊比較不足，再決定怎麼補。`;
      case 'critical':
        return ok
          ? '重大疾病的治療費與休養期間的收入損失，目前都有一次給付可以應對。各家對「重大疾病」的定義與給付條件不同，建議定期確認。'
          : `確診重大疾病或癌症時，治療加上無法工作的收入損失，可能還缺約 ${g}。一次給付型的重大疾病或癌症保障常被用來補這一塊，了解時請特別留意給付條件與疾病定義。`;
      default:
        return ok
          ? '失能或長期照護的費用與收入中斷，目前看起來有足夠的準備。政府長照資源與社會保險給付沒有計入本試算，若有可作為額外緩衝。'
          : `失能或長期照護是持續時間最長的風險，目前可能還缺約 ${g}。可以了解「失能扶助金」或「長照險」這類每月給付型保障，並確認給付條件（例如失能等級、日常生活能力的判定方式）。`;
    }
  }

  /* ========== 畫出報告 ========== */
  function badge(status) {
    return el('span', { class: 'badge ' + status.key }, status.text);
  }

  function summaryBlock(cats) {
    const totalGap = cats.reduce((t, c) => t + c.gap, 0);
    const totalNeed = cats.reduce((t, c) => t + c.need, 0);
    const covered = totalNeed - totalGap;
    const top = cats.slice().sort((a, b) => b.gap - a.gap)[0];

    if (totalGap === 0) {
      return el('div', { class: 'summary is-ok' },
        el('p', { class: 'summary-label' }, '你的結果'),
        el('p', { class: 'summary-num' }, '四類保障都足夠'),
        el('p', { class: 'summary-text' }, '以你填寫的條件來看，壽險、醫療、重大疾病與失能長照都有足夠的準備。之後若生活有變動（結婚、生子、換工作、買房），記得回來重新試算。')
      );
    }
    return el('div', { class: 'summary' },
      el('p', { class: 'summary-label' }, '四項缺口加總約'),
      el('p', { class: 'summary-num' }, wan(totalGap)),
      el('p', { class: 'summary-text' }, `缺口最大的是「${top.short}」，約 ${wan(top.gap)}，可以先從這一項開始了解。四類風險合計需要約 ${wan(totalNeed)}，你目前已準備約 ${wan(covered)}（${Math.round(covered / totalNeed * 100)}%）。`),
      el('p', { class: 'summary-foot' }, '這四項是不同的情境，不會同時發生。加總只是讓你了解整體規模，不代表每一項都要補滿。')
    );
  }

  function chartBlock(cats) {
    const maxNeed = Math.max(...cats.map((c) => c.need));
    const rows = cats.map((c) => {
      const width = maxNeed > 0 ? Math.max(c.need / maxNeed * 100, 6) : 100;
      const coverPct = c.need > 0 ? (c.need - c.gap) / c.need * 100 : 100;
      const fill = el('div', { class: 'bar-fill' + (coverPct >= 100 ? ' full' : ''), style: `width:${coverPct.toFixed(1)}%` });
      const track = el('div', {
        class: 'bar-track',
        role: 'img',
        'aria-label': `${c.title}：需要 ${wan(c.need)}，已準備 ${wan(c.need - c.gap)}，缺口 ${wan(c.gap)}`,
        style: `width:${width.toFixed(1)}%`
      }, fill);
      return el('div', { class: 'bar-row' },
        el('div', { class: 'bar-head' },
          el('img', { src: c.icon, alt: '', width: 32, height: 32 }),
          el('strong', null, c.title),
          badge(c.status)
        ),
        track,
        el('p', { class: 'bar-nums' },
          el('span', null, '需要 ', el('b', null, wan(c.need))),
          el('span', null, '已準備 ', el('b', null, wan(c.need - c.gap))),
          el('span', null, '缺口 ', el('b', null, wan(c.gap)))
        )
      );
    });
    return el('div', { class: 'panel' },
      el('h3', null, '四種保障一覽'),
      el('p', { class: 'panel-desc' }, '長條長度代表需求的大小，綠色是你已準備好的部分，斜線是缺口。'),
      rows,
      el('div', { class: 'legend' },
        el('span', null, el('i', { class: 'l-cover' }), '已準備'),
        el('span', null, el('i', { class: 'l-gap' }), '缺口')
      )
    );
  }

  function tableRows(rows) {
    return rows.map((r) =>
      el('tr', null,
        el('th', { scope: 'row' }, r.label, r.note ? el('small', null, r.note) : null),
        el('td', null, wan(r.value))
      )
    );
  }

  function detailBlock(c) {
    const table = el('table', { class: 'calc-table' },
      el('caption', { class: 'sr-only' }, `${c.title}的計算明細`),
      el('tbody', null,
        el('tr', { class: 'group' }, el('th', { colspan: 2, scope: 'colgroup' }, '需要準備')),
        tableRows(c.needRows),
        el('tr', { class: 'sum' }, el('th', { scope: 'row' }, '合計需要'), el('td', null, wan(c.need))),
        el('tr', { class: 'group' }, el('th', { colspan: 2, scope: 'colgroup' }, '你目前已有')),
        tableRows(c.haveRows),
        el('tr', { class: 'sum' }, el('th', { scope: 'row' }, '合計已有'), el('td', null, wan(c.have)))
      )
    );
    return el('section', { class: 'panel', 'aria-label': c.title },
      el('div', { class: 'detail-head' },
        el('img', { src: c.icon, alt: '', width: 48, height: 48 }),
        el('h3', null, c.title),
        badge(c.status)
      ),
      el('div', { class: 'stats' },
        el('div', { class: 'stat' }, el('span', null, '需要'), statValue(c.need)),
        el('div', { class: 'stat' }, el('span', null, '已有'), statValue(c.have)),
        el('div', { class: 'stat gap' + (c.gap === 0 ? ' zero' : '') }, el('span', null, '缺口'), statValue(c.gap))
      ),
      table,
      el('p', { class: 'advice' }, c.advice),
      c.extra ? el('p', { class: 'extra' }, c.extra) : null
    );
  }

  function assumptionsBlock(v) {
    const groups = [
      ['基本狀況', [
        ['現在年齡', `${v.age} 歲`],
        ['預計工作到', `${v.retireAge} 歲`],
        ['平均每月收入', wan(v.monthlyIncome)]
      ]],
      ['壽險', [
        ['家人每月開銷', wan(v.familyMonthly)],
        ['照顧年數', `${nf1.format(v.supportYears)} 年`],
        ['負債餘額', wan(v.debt)],
        ['子女人數', `${v.kids} 位`],
        ['每位教育預備金', wan(v.eduPerKid)],
        ['身後費用', wan(v.finalExpense)],
        ['可動用存款與投資', wan(v.savings)],
        ['目前壽險保額', wan(v.lifeCover)]
      ]],
      ['醫療', [
        ['住院天數', `${v.hospDays} 天`],
        ['病房差額', yuan(v.roomDiff) + '／日'],
        ['看護費', yuan(v.nurse) + '／日'],
        ['自費醫療項目', wan(v.selfPay)],
        ['目前每日住院給付', yuan(v.dailyCover) + '／日'],
        ['實支實付額度', wan(v.reimburse)]
      ]],
      ['重大疾病與失能長照', [
        ['自費治療費用', wan(v.ciTreat)],
        ['休養期間', `${v.ciMonths} 個月`],
        ['重疾險一次給付', wan(v.ciCover)],
        ['每月照護費用', wan(v.careMonthly)],
        ['照護年數', `${nf1.format(v.careYears)} 年`],
        ['無法工作年數', `${nf1.format(v.workLossYears)} 年`],
        ['失能／長照一次給付', wan(v.disLump)],
        ['失能／長照每月給付', wan(v.disMonthly)]
      ]]
    ];
    return el('section', { class: 'panel', 'aria-label': '試算條件' },
      el('h3', null, '這份報告用到的條件'),
      el('p', { class: 'panel-desc' }, '結果會隨著下列數字改變。標示「參考值」的項目是概略估算，不是官方統計，請依自己的狀況調整後再看結果。'),
      el('div', { class: 'assume' },
        groups.map(([title, items]) =>
          el('div', null,
            el('h4', null, title),
            el('dl', null, items.map(([k, val]) => [el('dt', null, k), el('dd', null, val)]))
          )
        )
      )
    );
  }

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
    return el('section', { class: 'panel cta', 'aria-label': '聯絡方式' },
      el('h3', null, '想把結果和專業人員一起檢視嗎？'),
      el('p', null, name
        ? `歡迎聯絡${name}，一起看看哪些缺口值得優先處理。`
        : '把這份報告帶著，和專業人員討論最適合你的做法。'),
      el('div', { class: 'cta-buttons no-print' }, buttons),
      el('p', { class: 'print-only' }, (name ? name + '　' : '') + printLines.join('　'))
    );
  }

  function render(v) {
    const cats = calculate(v);
    const today = new Date().toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric' });

    const actions = el('div', { class: 'report-actions' },
      el('button', { type: 'button', class: 'btn', id: 'print-btn' }, '列印／存成 PDF'),
      el('button', { type: 'button', class: 'btn btn-ghost', id: 'back-btn' }, '回去修改數字')
    );

    report.replaceChildren(
      el('div', { class: 'container' },
        el('h2', { class: 'report-title', id: 'report-title' }, '你的保障缺口報告'),
        el('p', { class: 'report-meta' }, `${CFG.siteName}｜試算日期：${today}`),
        summaryBlock(cats),
        chartBlock(cats),
        cats.map(detailBlock),
        assumptionsBlock(v),
        contactBlock(),
        actions,
        el('p', { class: 'report-disclaimer' }, '本報告為教育性質的簡化試算，不構成保險、投資或法律建議，也不是任何商品的推薦。未計入勞保、國保、健保與政府長照資源等社會保險及補助；實際保障內容以保單條款為準。你填寫的資料只在這個瀏覽器裡計算，不會被上傳或儲存。')
      )
    );
    report.setAttribute('aria-labelledby', 'report-title');
    report.hidden = false;

    document.getElementById('print-btn').addEventListener('click', printReport);
    document.getElementById('back-btn').addEventListener('click', () => scrollToId('calc'));

    report.focus({ preventScroll: true });
    scrollToId('report');
  }

  function scrollToId(id) {
    document.getElementById(id).scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
  }

  function printReport() {
    const oldTitle = document.title;
    document.title = '保障缺口報告';
    window.print();
    document.title = oldTitle;
  }

  /* ========== 事件 ========== */
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    clearAllErrors();
    const { values, errors } = readForm();

    if (errors.length) {
      errors.forEach((err) => setFieldError(document.getElementById(err.id), err.msg));
      formError.textContent = `有 ${errors.length} 個欄位需要修正，已用紅字標示在欄位下方。`;
      formError.hidden = false;
      report.hidden = true;
      const first = document.getElementById(errors[0].id);
      first.focus({ preventScroll: true });
      first.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'center' });
      return;
    }
    render(values);
  });

  // 使用者開始修改某個欄位時，先把它的錯誤訊息清掉
  form.addEventListener('input', (e) => {
    if (e.target.id in FIELDS && e.target.getAttribute('aria-invalid') === 'true') {
      setFieldError(e.target, '');
    }
  });

  resetBtn.addEventListener('click', () => {
    form.reset(); // 參考值會回到預設，其他欄位清空
    clearAllErrors();
    report.hidden = true;
    report.replaceChildren();
    document.getElementById('age').focus();
  });
})();
