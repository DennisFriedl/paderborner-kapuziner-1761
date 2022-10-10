# Kontrolliert, ob die Keys nocheinmal in einer anderen XML-Datei vorkommen.

from lxml import etree

parser = etree.XMLParser(remove_blank_text=False)
namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace"}


az_xml_text = open("XML/Auszeichnung/kapuziner_pb.xml", "r", encoding="utf-8")
az_tree = etree.parse(az_xml_text, parser)
az_root = az_tree.getroot()
az_keys = az_root.xpath(".//@key", namespaces=namespaces)

or_xml_text = open("XML/Register/register_orte.xml", "r", encoding="utf-8")
or_tree = etree.parse(or_xml_text, parser)
or_root = or_tree.getroot()
or_keys = or_root.xpath(".//@key | //@xml:id", namespaces=namespaces)


pr_xml_text = open("XML/Register/register_personen.xml", "r", encoding="utf-8")
pr_tree = etree.parse(pr_xml_text, parser)
pr_root = pr_tree.getroot()
pr_keys = pr_root.xpath(".//@key | //@xml:id", namespaces=namespaces)


wr_xml_text = open("XML/Register/register_werke.xml", "r", encoding="utf-8")
wr_tree = etree.parse(wr_xml_text, parser)
wr_root = wr_tree.getroot()
wr_keys = wr_root.xpath(".//@key | //@xml:id", namespaces=namespaces)


org_xml_text = open("XML/Register/register_organisationen.xml", "r", encoding="utf-8")
org_tree = etree.parse(org_xml_text, parser)
org_root = org_tree.getroot()
org_keys = org_root.xpath(".//@key | //@xml:id", namespaces=namespaces)

allKeys = az_keys + or_keys + pr_keys + wr_keys + org_keys


for key in allKeys:
    if allKeys.count(key) < 2:
        print(key)
