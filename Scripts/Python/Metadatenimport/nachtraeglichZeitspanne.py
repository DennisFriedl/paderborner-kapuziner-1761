# Guckt bei Jahresdaten aus Wikidata, ob Centuries oder Dekades gemeint sind

from lxml import etree
import requests
import time

parser = etree.XMLParser(remove_blank_text=False)

pr_xml_text = open("XML/Register/register_personen.xml", "r", encoding="utf-8")
pr_tree = etree.parse(pr_xml_text, parser)
pr_root = pr_tree.getroot()

namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace", "owl": "http://www.w3.org/2002/07/owl#", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "gn": "http://www.geonames.org/ontology#", "foaf": "http://xmlns.com/foaf/0.1/", "wdt": "http://www.wikidata.org/prop/direct/", "schema": "http://schema.org/", "gndo": "https://d-nb.info/standards/elementset/gnd#", "rdfs": "http://www.w3.org/2000/01/rdf-schema#" ,"wgs84_pos": "http://www.w3.org/2003/01/geo/wgs84_pos#", "psv": "http://www.wikidata.org/prop/statement/value/", "wikibase": "http://wikiba.se/ontology#"}

tei = "{%s}" % namespaces["tei"]
xml = "{%s}" % namespaces["xml"]

pr_persons = pr_root.xpath(".//tei:body//tei:listPerson//tei:person", namespaces=namespaces)

def look_wikidata(person):
    if person.xpath(".//tei:date[contains(@source, 'wikidata')]", namespaces=namespaces):
        wikidata_id = person.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces)[0].text
        r = requests.get(f" https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.rdf?flavor=dump")
        time.sleep(1)
        wikidata_tree_root = etree.fromstring(r.content)
        birth_precision_key= wikidata_tree_root.xpath(f".//psv:P569/@rdf:resource", namespaces=namespaces)
        death_precision_key = wikidata_tree_root.xpath(f".//psv:P570/@rdf:resource", namespaces=namespaces)
        birth_precision = 10
        death_precision = 10
        if birth_precision_key:
            birth_precision = int(wikidata_tree_root.xpath(f".//rdf:Description[@rdf:about='{birth_precision_key[0]}']/wikibase:timePrecision", namespaces=namespaces)[0].text)
        if death_precision_key:
            death_precision = int(wikidata_tree_root.xpath(f".//rdf:Description[@rdf:about='{death_precision_key[0]}']/wikibase:timePrecision", namespaces=namespaces)[0].text)

        if birth_precision < 9 or death_precision < 9:
            print(wikidata_id)

for person in pr_persons:
    look_wikidata(person)

print("___________ FINISHED _____________")

