from __future__ import annotations

from agent.cdp_client import CdpClient

# JavaScript das PAT25 Labels aus dem Chart liest.
# Exakt dieselbe Logik wie tradingview-mcp/src/core/data.js buildGraphicsJS()
_LABELS_JS = """
(function() {
  try {
    var chart = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget;
    var model = chart.model();
    var sources = model.model().dataSources();
    var results = [];
    for (var si = 0; si < sources.length; si++) {
      var s = sources[si];
      if (!s.metaInfo) continue;
      try {
        var meta = s.metaInfo();
        var name = meta.description || meta.shortDescription || '';
        if (name.indexOf('PAT25') === -1) continue;
        var g = s._graphics;
        if (!g || !g._primitivesCollection) continue;
        var pc = g._primitivesCollection;
        var outer = pc.dwglabels;
        if (!outer) continue;
        var inner = outer.get('labels');
        if (!inner) continue;
        var coll = inner.get(false);
        if (!coll || !coll._primitivesDataById) continue;
        coll._primitivesDataById.forEach(function(v) {
          var txt = v._data ? (v._data.text || '') : '';
          var price = v._data ? (v._data.price || v._data.y || 0) : 0;
          if (txt && price) results.push({text: txt, price: price});
        });
      } catch(e) {}
    }
    return results;
  } catch(e) { return []; }
})()
"""

_CURRENT_BAR_JS = """
(function() {
  try {
    var bars = window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().mainSeries().bars();
    var idx = bars.lastIndex();
    var v = bars.valueAt(idx);
    if (!v) return null;
    return {time: v[0], open: v[1], high: v[2], low: v[3], close: v[4], volume: v[5] || 0};
  } catch(e) { return null; }
})()
"""


class ChartReader:
    def __init__(self, cdp: CdpClient):
        self._cdp = cdp

    def get_pat25_labels(self) -> list[dict]:
        """Liest alle PAT25 Session-Labels vom Chart. Gibt [] zurück wenn keine da."""
        result = self._cdp.evaluate(_LABELS_JS)
        if not result:
            return []
        return result

    def get_current_bar(self) -> dict | None:
        """Liest den letzten Bar (OHLCV + Timestamp) vom Chart."""
        return self._cdp.evaluate(_CURRENT_BAR_JS)

    def labels_as_dict(self) -> dict[str, float]:
        """Gibt PAT25 Labels als {text: price} Dict zurück."""
        return {lbl["text"]: lbl["price"] for lbl in self.get_pat25_labels()}
