import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const html=fs.readFileSync(new URL('../web/index.html',import.meta.url),'utf8');
const app=fs.readFileSync(new URL('../web/app.js',import.meta.url),'utf8');
const visualization=fs.readFileSync(new URL('../web/visualization.js',import.meta.url),'utf8');
const visualizationCSS=fs.readFileSync(new URL('../web/visualization.css',import.meta.url),'utf8');
const compactHTML=html.replace(/\s+/g,' ');

test('後分類使用固定中文分段控制與緊湊工具列',()=>{
 assert.match(compactHTML,/role="tab" data-type="Metadata"[^>]*>後設資料<\/button>/);
 assert.match(compactHTML,/role="tab" data-type="Tag"[^>]*>內文標籤<\/button>/);
 assert.match(html,/class="facet-tools"/);
 assert.match(html,/id="clear-facets">清除全部<\/button>/);
 assert.match(html,/同欄多選採 OR/);
 assert.doesNotMatch(html,/>Metadata<\/option>|>Tag<\/option>/);
});

test('分段控制支援選取狀態、方向鍵及中文條件來源',()=>{
 assert.match(app,/setAttribute\('aria-selected'/);
 assert.match(app,/ArrowLeft','ArrowRight/);
 assert.match(app,/內文標籤':'後設資料/);
});

test('視覺化入口與共用控制存在，泡泡圖可操作且未完成圓餅圖不可操作',()=>{
 assert.match(html,/id="visualize">視覺化<\/button>/);
 assert.match(html,/id="viz-search"/);
 assert.match(html,/id="viz-zoom"[^>]*min="10"[^>]*max="200"/);
 assert.match(html,/id="viz-zoom"[^>]*step="1"/);
 assert.match(html,/data-view="bubble"[^>]*>泡泡圖<\/button>/);
 assert.match(html,/圓餅圖（後續開放）<\/button>/);
 assert.equal((html.match(/後續開放）<\/button>/g)||[]).length,1);
 assert.match(html,/data-view="table"[^>]*>資料表格<\/button>/);
 assert.match(html,/id="viz-export" hidden>↓ 匯出 CSV<\/button>/);
 assert.match(visualization,/prepareTableRows/);
 assert.match(visualization,/this\.state\.zoom\[this\.state\.view\]/);
 assert.match(visualizationCSS,/\.viz-data-table/);
 assert.match(visualizationCSS,/\.viz-bubble-node/);
 assert.match(visualization,/bar\.title=`\$\{item\.label\}：\$\{item\.count\}筆`/);
 assert.match(visualization,/make\('span','分析標的','viz-source-label'\)/);
 assert.match(visualization,/this\.chart\.scrollTop=0/);
 assert.match(html,/id="viz-fullscreen"/);
 assert.match(visualization,/wheelVisualizationZoom/);
 assert.match(visualization,/toggleFullscreen/);
 assert.match(app,/facet-field-heading/);
 assert.match(app,/visualize-icon/);
 assert.match(visualizationCSS,/\.facet-field-heading #visualize/);
 const labelSize=Number(visualizationCSS.match(/\.facet-field-heading label,\s*\.facet-tools label\s*\{[^}]*font-size:\s*(\d+)px/s)?.[1]);
 const entrySize=Number(visualizationCSS.match(/\.facet-field-heading #visualize\s*\{[^}]*font-size:\s*(\d+)px/s)?.[1]);
 assert.ok(labelSize>entrySize,'控制標籤應大於視覺化按鈕文字');
 assert.match(visualizationCSS,/\.viz-navigation #viz-back\s*\{[^}]*font-size:\s*14px/s);
 assert.match(visualizationCSS,/\.viz-chart\.viz-dense \.viz-count\s*\{[^}]*opacity:\s*1/s);
});
