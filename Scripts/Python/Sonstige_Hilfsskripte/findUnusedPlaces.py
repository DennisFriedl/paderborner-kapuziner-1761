from lxml import etree

parser = etree.XMLParser(remove_blank_text=False)

or_xml_text = open("XML/Register/register_orte.xml", "r", encoding="utf-8")
or_tree = etree.parse(or_xml_text, parser)
or_root = or_tree.getroot()

auszeichnung_xml_text = open("XML/Auszeichnung/kapuziner_pb.xml", "r", encoding="utf-8").read()
wr_xml_text = open("XML/Register/register_werke.xml", "r", encoding="utf-8").read()
pr_xml_text = open("XML/Register/register_personen.xml", "r", encoding="utf-8").read()



namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace"}

tei = "{%s}" % namespaces["tei"]
xml = "{%s}" % namespaces["xml"]

or_places = or_root.xpath(".//tei:body//tei:listPlace//tei:place", namespaces=namespaces)

for i, place in enumerate(or_places):
    place_id = place.xpath("./@xml:id", namespaces=namespaces)[0]
    if place_id not in auszeichnung_xml_text and place_id not in wr_xml_text and place_id not in pr_xml_text:
        place.getparent().remove(place)

or_tree.write("XML/Register/register_orte.xml", encoding="utf-8", pretty_print=True)