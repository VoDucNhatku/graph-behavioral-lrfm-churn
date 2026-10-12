"""Validate all final pages and render contact sheets for visual inspection."""
from pathlib import Path
import hashlib
import json
import re
import unicodedata
import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'output/pdf'
TEMP=ROOT/'tmp/pdfs/qa'
EVIDENCE=ROOT/'docs/vietnamese/evidence'


def clean(text):
    return ''.join(c for c in unicodedata.normalize('NFKC',text).lower() if c.isalnum())


if __name__=='__main__':
    TEMP.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16) if Path('C:/Windows/Fonts/arial.ttf').exists() else ImageFont.load_default()
    results=[]
    pdfs=sorted(OUTPUT.glob('0*.pdf'))
    assert len(pdfs)==4, 'All four requested PDFs must exist.'
    for pdf in pdfs:
        doc=fitz.open(pdf)
        page_records=[]
        all_text=[]
        body_text=[]
        thumbnails=[]
        for index,page in enumerate(doc):
            text=page.get_text()
            all_text.append(text)
            assert '\ufffd' not in text and '\u25a0' not in text, f'Replacement/missing glyph on {pdf.name}:{index+1}'
            assert len(text.strip())>35, f'Empty page on {pdf.name}:{index+1}'
            errors=[]
            for block in page.get_text('dict')['blocks']:
                if block['type']!=0:
                    continue
                for line in block['lines']:
                    x0,y0,x1,y1=line['bbox']
                    if y0>=50 and y1<=page.rect.height-45:
                        body_text.append(''.join(span['text'] for span in line['spans']))
                    if x0<43 or x1>page.rect.width-43 or y0<14 or y1>page.rect.height-13:
                        errors.append([round(v,2) for v in line['bbox']])
            assert not errors, f'Text beyond safe bounds on {pdf.name}:{index+1}: {errors}'
            font_names=sorted({f[3] for f in page.get_fonts()})
            page_records.append({'page':index+1,'characters':len(text),'fonts':font_names,'text_within_safe_bounds':True})
            pix=page.get_pixmap(matrix=fitz.Matrix(.65,.65),alpha=False)
            image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
            image.thumbnail((365,516))
            thumb=Image.new('RGB',(385,548),'#E8ECEF')
            thumb.paste(image,((385-image.width)//2,22))
            ImageDraw.Draw(thumb).text((12,525),f'{pdf.name[:2]} | page {index+1}',font=font,fill='#203044')
            thumbnails.append(thumb)
        text='\n'.join(all_text)
        assert 'tiếng việt' in text.lower()
        assert len(doc.get_toc())>=10
        for group_start in range(0,len(thumbnails),6):
            group=thumbnails[group_start:group_start+6]
            sheet=Image.new('RGB',(385*3,548*2),'white')
            for position,thumbnail in enumerate(group):
                sheet.paste(thumbnail,((position%3)*385,(position//3)*548))
            sheet.save(TEMP/f'{pdf.stem}-sheet-{group_start//6+1}.png')
        (TEMP/(pdf.stem+'.txt')).write_text(text,encoding='utf-8')
        # Source paragraphs are represented as text, while mathematics and figures
        # are images whose fidelity is verified separately by source coverage.
        source=ROOT/'docs/vietnamese'/({'01':'01-kien-thuc-nen-tang.md','02':'02-quy-trinh-nghien-cuu.md',
                                      '03':'03-ban-dich-paper.md','04':'04-bao-cao-tong-hop.md'}[pdf.name[:2]])
        source_lines=source.read_text(encoding='utf-8').splitlines()
        snippets=[]
        inside_code=False
        inside_math=False
        for line in source_lines:
            stripped=line.strip()
            if stripped.startswith('```'):
                inside_code=not inside_code
                continue
            if stripped.startswith('$$'):
                if stripped.count('$$')<2:
                    inside_math=not inside_math
                continue
            if inside_code or inside_math or stripped.startswith(('#','|','!','>')) or len(stripped)<65:
                continue
            candidate=re.sub(r'\$[^$]+\$','',stripped)
            candidate=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1',candidate)
            candidate=re.sub(r'[*`]','',candidate)
            normalized=clean(candidate)
            if len(normalized)>=45:
                snippets.append(normalized)
        pdf_text=clean('\n'.join(body_text))
        missing=[s for s in snippets if s not in pdf_text]
        assert not missing, f'Prose rendering omissions on {pdf.name}: {missing[:4]}'
        results.append({'pdf':pdf.relative_to(ROOT).as_posix(),'pages':len(doc),'bytes':pdf.stat().st_size,
                        'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'outline_entries':len(doc.get_toc()),
                        'prose_snippets_checked':len(snippets),'prose_snippets_missing':0,'page_checks':page_records})
    path=EVIDENCE/'pdf-validation.json'
    path.write_text(json.dumps({'status':'structural_checks_passed','visual_review':'contact sheets generated; manual review required',
                                'documents':results},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{k:r[k] for k in ['pdf','pages','bytes','outline_entries','prose_snippets_checked']} for r in results],indent=2))
