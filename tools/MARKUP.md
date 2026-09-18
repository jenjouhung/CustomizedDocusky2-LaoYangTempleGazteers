# 全文標記解析模組

入口：`markup.parse_text(source, allowed)`。輸入為全文原始值與允許的 Tagname 集合；輸出為 `text` 純文字及 `tags` 陣列。錯誤以 `ValueError` 回報，由匯入器補上工作表、列與欄位。

每個 Tag 保存 name、term、refId、text、start、end。位置單位為 Unicode code point，結束位置不含在區間內。原始欄位不改寫；未知 Tag、巢狀、缺 Term、無效 XML 或宣告均拒絕。

`packages.py` 將原始紀錄保存在 records/，解析結果保存在 texts/。schema 2 的全文索引取純文字；facets.json 保留原 Metadata 數字欄位識別，新增 `tag:Tagname` 識別，文件 ID 去重。schema 1 由前端維持原始純文字讀取，不必覆寫舊版本。

公開前端使用 `web/core/facet-fields.js` 取得兩類選單與名稱，既有 facets.js/state.js 繼續負責集合運算。標籤文案由 `dataset/profile.json` 的 `tagFacets` 設定，`tools/config.py`只負責驗證及推導索引；更改標籤後新建立版本保存新設定，已封存版本保留快照。

全文背景與高亮入口為 `web/core/text-view.js` 的 `renderText(parsed, terms, conditions)`，回傳安全的正文節點。`segments` 為可獨立測試的純函式，負責位置轉換及Tag、正式過濾、搜尋的分段狀態。共用樣式集中於 web/style.css；測試為 tests/text-view.test.js 及 tests/tag-browser.cjs。

驗證：`python3 -m unittest discover -s tests -p 'test_*.py'`、`npm test` 及 `tests/tag-browser.cjs`。瀏覽器測試使用 PLAYWRIGHT_MODULE 指定已安裝 Playwright 的模組路徑，TAG_TEST_URL 指向測試靜態網站。
