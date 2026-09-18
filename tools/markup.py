"""Parse flat research XML fragments. Offsets are Unicode code points, end exclusive."""
import re
import xml.etree.ElementTree as ET

PARSER_VERSION = 1


def parse_text(source, allowed):
    raw = str(source)
    if '<' not in raw:
        return {'text': raw, 'tags': []}
    if re.search(r'<!|<\?', raw):
        raise ValueError('不允許宣告、DTD、註解或處理指令')
    try:
        root = ET.fromstring('<root>' + raw + '</root>')
    except ET.ParseError as exc:
        raise ValueError(f'全文標記格式錯誤：{exc}') from exc
    text = root.text or ''
    tags = []
    for node in root:
        if node.tag not in allowed:
            raise ValueError(f'未知 Tag {node.tag}，請回到資料規格確認')
        if len(node):
            raise ValueError(f'{node.tag} 不允許巢狀標記')
        if 'term' in node.attrib and 'Term' in node.attrib:
            raise ValueError(f'{node.tag} 同時使用 term 與 Term')
        term = node.get('term', node.get('Term'))
        if term is None or not term.strip():
            raise ValueError(f'{node.tag} 缺少或空白 Term')
        content = node.text or ''
        if not content.strip():
            raise ValueError(f'{node.tag} 標記內容不得空白')
        tags.append({'name': node.tag, 'term': term, 'refId': node.get('RefId'),
                     'text': content, 'start': len(text), 'end': len(text) + len(content)})
        text += content + (node.tail or '')
    return {'text': text, 'tags': tags}
