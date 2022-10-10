# Hilfsscript, um schnell Anhand des Titels eine Sprache zuzuweisen

import os
from lxml import etree



parser = etree.XMLParser(remove_blank_text=False)

wr_xml_text = open("XML/Register/register_werke.xml", "r", encoding="utf-8")
wr_tree = etree.parse(wr_xml_text, parser)
wr_root = wr_tree.getroot()

namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace"}

tei = "{%s}" % namespaces["tei"]
xml = "{%s}" % namespaces["xml"]

wr_monographs = wr_root.xpath(".//tei:bibl[@type='m' and ./tei:textLang[@source='auto']]", namespaces=namespaces)

print(len(wr_monographs), "left")

for monograph in wr_monographs:
    series_title = " ".join(monograph.xpath("./parent::tei:bibl[@type='s']/tei:title//text()", namespaces=namespaces))
    monograph_title = " ".join(monograph.xpath("./tei:title//text()", namespaces=namespaces))

    print(series_title, monograph_title)
    print("1: Lat \n2: Deu \n5: Unsicher \n9: Exit")
    decision = input("Input:")
    if decision in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
        decision = int(decision)

    language = ""
    if decision not in [1, 2, 5, 9]:
        decision = 5
    if decision == 1 or decision == 2:
        if decision == 1:
            language = "lat"
        elif decision == 2:
            language = "deu"
        monograph.xpath("./tei:textLang", namespaces=namespaces)[0].attrib["mainLang"] = language
        monograph.xpath("./tei:textLang", namespaces=namespaces)[0].attrib["source"] = "guessed"
    elif decision == 5:
        pass
    elif decision == 9:
        break

        

    os.system('cls')

wr_tree.write("XML/Register/register_werke.xml", encoding="utf-8", pretty_print=True)

print("Finished")

