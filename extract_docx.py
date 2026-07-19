import zipfile
import xml.etree.ElementTree as ET
import os

docx_path = "Paper Title2.docx"
txt_path = "paper_title_2.txt"

if not os.path.exists(docx_path):
    print(f"Error: {docx_path} does not exist.")
    exit(1)

try:
    with zipfile.ZipFile(docx_path) as z:
        xml_content = z.read("word/document.xml")
        root = ET.fromstring(xml_content)
        
        # Word document XML uses namespaces
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        paragraphs = []
        for para in root.findall('.//w:p', namespaces):
            texts = []
            for run in para.findall('.//w:t', namespaces):
                if run.text:
                    texts.append(run.text)
            paragraphs.append("".join(texts))
        
        text = "\n".join(paragraphs)
        
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
            
        print(f"Success: Extracted {len(paragraphs)} paragraphs to {txt_path}.")
except Exception as e:
    print(f"Error: {e}")
