"""Monta gerador_documentos/Gerador_Acompanhamento_Periodico.html (arquivo único, funciona offline):
template + bibliotecas de vendor/ + modelo .docx embutido em base64.

Rode depois de alterar o template, as bibliotecas ou o modelo .docx:
    python gerador_documentos/html/montar_html.py
"""
import base64
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PASTA = AQUI.parent
MODELO = PASTA / "Modelo_Documento_de_Acompanhamento_Quadrimestral_do_Auditor.docx"
SAIDA = PASTA / "Gerador_Acompanhamento_Periodico.html"
VENDOR = ["xlsx.core.min.js", "pizzip.min.js", "docxtemplater.min.js"]  # SheetJS 0.18.5, PizZip 3.3.0, docxtemplater 3.71.1

html = (AQUI / "gerador.template.html").read_text(encoding="utf-8")
libs = "\n".join((AQUI / "vendor" / v).read_text(encoding="utf-8") for v in VENDOR)
libs = libs.replace("</script", "<\\/script")  # segurança ao embutir em <script>
assert html.count("/*VENDOR*/") == 1 and html.count("__MODELO_B64__") == 1
html = html.replace("/*VENDOR*/", libs).replace("__MODELO_B64__", base64.b64encode(MODELO.read_bytes()).decode())
SAIDA.write_text(html, encoding="utf-8")
print(f"Gerado: {SAIDA} ({SAIDA.stat().st_size / 1024:.0f} KB)")
