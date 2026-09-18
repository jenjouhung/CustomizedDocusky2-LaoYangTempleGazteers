# 規格書索引

本資料夾集中保存專案規格。各文件的責任如下：

- [`DEVELOPMENT_SPEC.md`](DEVELOPMENT_SPEC.md)：共用系統功能、運作邏輯、介面、架構及整體測試規格。
- [`Data_SPEC.md`](Data_SPEC.md)：本研究資料的欄位、類型、後分類、顯示、排序及驗證設定。
- [`VISUALIZATION_SPEC.md`](VISUALIZATION_SPEC.md)：視覺化共用控制、已實作的長條圖、泡泡圖與資料表格，以及後續圓餅圖規劃。
- [`DATASET_ADAPTATION_PROMPT.md`](DATASET_ADAPTATION_PROMPT.md)：把平台改用另一份 Excel 時，可直接交給 AI Agent 的單一 Prompt 首版建置流程、自動推定原則與最小修改邊界。

建立其他研究資料平台時，原則上沿用開發及視覺化共用規格，另行確認或建立該資料集的資料規格。機器可讀設定集中於`../dataset/profile.json`，資料專屬驗收值集中於`../dataset/acceptance.json`；兩者必須與`Data_SPEC.md`一致。
