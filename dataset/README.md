# 資料集設定入口

此資料夾是將平台改用另一份 Excel 時的主要修改邊界。一般資料格式移植不應修改 `web/`、`tools/importer.py`、查詢、後分類或視覺化核心。

- `profile.json`：唯一的機器可讀資料設定。以 Excel 欄名宣告欄位順序、類型、必填、唯一鍵、題名、全文、結果顯示、Metadata 後分類、排序、多值分隔、Tag 後分類、網站名稱及分享資訊；程式會自動換算欄位索引。
- `acceptance.json`：資料專屬測試的範例檔相對路徑、預期筆數、欄數與 Tag 統計。它不是系統邏輯，也不會進入公開資料包。
- `../SPEC/Data_SPEC.md`：供人檢查與確認的資料規格。內容必須與 `profile.json`、`acceptance.json` 一致。
- `../SPEC/DATASET_ADAPTATION_PROMPT.md`：可交給 LLM 執行下一個資料集移植的提示詞。

預設為「單一 Prompt 首版建置」流程：

1. 在獨立的專案副本中放入新 Excel。
2. 執行 `python3 tools/inspect_excel.py 新資料.xlsx`，先取得精簡結構報告。
3. Agent 依 `../SPEC/DATASET_ADAPTATION_PROMPT.md` 的預設推定規則，直接產生可運作首版；不要求使用者先回答完整欄位問卷。
4. 只修改上述三份資料專屬文件，並將人為指定與「首版自動推定」清楚區分。
5. 執行 `python3 tools/config.py` 驗證設定。
6. 執行 `python3 tools/create_dataset.py 新資料.xlsx --replace`，備份並取代副本中的舊資料，建立新的 `v0001` 與 `public-build/`。
7. 執行完整測試與關鍵瀏覽器流程抽查。只有測試證明共用程式無法表達新資料時，才擴大修改範圍。
8. 完成後再請使用者依研究語意微調欄位用途、顯示名稱、後分類順序與配色等細節。

`create_dataset.py --replace` 會先驗證新 Excel，再將既有資料備份至 `backups/`；請勿在仍需保留原平台運作狀態的唯一工作副本上使用。

第一次建置只在 Excel 無法讀取、標題列無效、無唯一鍵、無全文候選或 Tag 無法解析等阻斷情形下中斷詢問。其他不確定項目應以可反悔的預設建立首版。
