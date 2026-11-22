() => {
  // create の手順 7 の DOM 検査。browser_evaluate の function に、中身を変えずにそのまま渡す。
  // 戻り値: { violations, protocol, file }。violations が空で、protocol が "file:" で、
  // file が保存したファイル名と一致すれば通る（一致しなければ、移動したので不正）。
  const violations = [];
  const add = (el, why) => violations.push(el.localName + ": " + why);

  // template と noscript は、中身が querySelectorAll で走査されないため、要素ごと不正にする。
  const banned = ["template", "noscript", "iframe", "frame", "object", "embed", "base", "form"];

  // URL の判定。値の前後の空白と、途中のタブ・改行を除いてから判定する。
  // 属性名が href で終わるもの（xlink:href を含む）の、# で始まる値だけは対象外
  // （SVG の <use href="#id">、目次の <a href="#章">）。src は # で始まっても下の許可リストで判定する。
  // それ以外は new URL(値, location.href) の protocol で判定する（文字列の先頭一致では判定しない）。
  // 許すのは、a の href・xlink:href の http:・https:・mailto:（素材由来の文字リンク）と、
  // img の src の data:（値が data:image/ で始まるもの）だけ。new URL が例外を投げた値は不正。
  const checkUrl = (el, name, raw) => {
    const value = raw.trim().replace(/[\t\n\r]/g, "");
    const isHref = name.endsWith("href");
    if (isHref && value.startsWith("#")) return;
    let protocol;
    try {
      protocol = new URL(value, location.href).protocol;
    } catch (e) {
      add(el, name + " の値を URL として読めない: " + value);
      return;
    }
    const tag = el.localName.toLowerCase();
    if (isHref && tag === "a" && ["http:", "https:", "mailto:"].includes(protocol)) return;
    if (name === "src" && tag === "img" && value.startsWith("data:image/")) return;
    add(el, name + " に許されない値: " + value);
  };

  for (const el of document.querySelectorAll("*")) {
    const tag = el.localName.toLowerCase();
    if (banned.includes(tag)) add(el, "使えない要素");

    for (const attr of el.attributes) {
      const name = attr.name.toLowerCase();
      // 属性名が on で始まるもの（イベント属性）。
      if (name.startsWith("on")) add(el, "イベント属性 " + name);
      if (name === "srcdoc") add(el, "srcdoc 属性");
      if (name === "action" || name === "formaction") add(el, name + " 属性");
      // meta の http-equiv は、content-security-policy だけを許す（refresh など）。
      if (tag === "meta" && name === "http-equiv") {
        if (attr.value.trim().toLowerCase() !== "content-security-policy") {
          add(el, "http-equiv=" + attr.value);
        }
      }
      if (name.endsWith("href") || name === "src") checkUrl(el, name, attr.value);
    }

    // SVG の animate・set・animateTransform など。attributeName が href・xlink:href・src
    // （名前空間つきを含む）のものだけを対象にして、to・from・values（; で分けた各値）に
    // 上の URL の判定を当てる。それ以外の attributeName（opacity など）は対象外。
    const target = el.getAttribute("attributeName");
    if (target !== null) {
      const local = target.trim().toLowerCase().split(":").pop();
      if (local === "href" || local === "src") {
        for (const key of ["to", "from", "values"]) {
          const raw = el.getAttribute(key);
          if (raw === null) continue;
          for (const part of key === "values" ? raw.split(";") : [raw]) {
            checkUrl(el, local, part);
          }
        }
      }
    }
  }

  return {
    violations,
    protocol: location.protocol,
    file: decodeURIComponent(location.pathname.split("/").pop()),
  };
}
