// Paste this whole script into browser DevTools Console on TikTok upload page.
(() => {
  const SELECTORS = {
    upload_input: [
      "input[type='file'][accept='video/*']",
      "input[type='file'][accept*='video']",
      "input[type='file']",
      "xpath=//input[@type='file' and contains(@accept,'video')]",
      "xpath=//input[@type='file']",
    ],
    description: [
      "xpath=//div[@contenteditable='true']",
      "div[contenteditable='true']",
    ],
    post_button: [
      "xpath=//button[@data-e2e='post_video_button']",
      "button[data-e2e='post_video_button']",
    ],
  };

  const LIMIT = 5;

  function queryAllWithXPathSupport(rootDoc, selector) {
    if (selector.startsWith("xpath=")) {
      const xp = selector.slice(6);
      const out = [];
      const it = rootDoc.evaluate(xp, rootDoc, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
      for (let i = 0; i < it.snapshotLength; i++) out.push(it.snapshotItem(i));
      return out;
    }
    return Array.from(rootDoc.querySelectorAll(selector));
  }

  function isVisible(el) {
    if (!(el instanceof Element)) return false;
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return s.display !== "none" && s.visibility !== "hidden" && r.width > 0 && r.height > 0;
  }

  function inspectDoc(doc, frameLabel) {
    const result = { frame: frameLabel, url: doc.URL, keys: {} };

    for (const [key, sels] of Object.entries(SELECTORS)) {
      result.keys[key] = [];
      for (const sel of sels) {
        let nodes = [];
        let err = null;
        try {
          nodes = queryAllWithXPathSupport(doc, sel);
        } catch (e) {
          err = String(e);
        }

        result.keys[key].push({
          selector: sel,
          count: nodes.length,
          error: err,
          sample: nodes.slice(0, LIMIT).map((el, idx) => ({
            index: idx,
            tag: el?.tagName || null,
            visible: el ? isVisible(el) : false,
            enabled: typeof el?.disabled === "boolean" ? !el.disabled : null,
            accept: el?.getAttribute?.("accept") || null,
            outerHTML: el?.outerHTML || null,
          })),
        });
      }
    }

    return result;
  }

  const reports = [];
  reports.push(inspectDoc(document, "main"));

  document.querySelectorAll("iframe").forEach((f, i) => {
    try {
      if (f.contentDocument) reports.push(inspectDoc(f.contentDocument, `iframe[${i}]`));
    } catch (e) {
      reports.push({ frame: `iframe[${i}]`, url: f.src, error: `cross-origin: ${String(e)}` });
    }
  });

  console.log(JSON.stringify(reports, null, 2));
})();
