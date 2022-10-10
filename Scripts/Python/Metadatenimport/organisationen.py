# Importiert Daten aus verknüpften Datenbanken für Organisationen

from lxml import etree
import requests
import time

parser = etree.XMLParser(remove_blank_text=False)

orgr_xml_text = open("XML/Register/register_organisationen.xml", "r", encoding="utf-8")
orgr_tree = etree.parse(orgr_xml_text, parser)
orgr_root = orgr_tree.getroot()

namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace", "owl": "http://www.w3.org/2002/07/owl#", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "gn": "http://www.geonames.org/ontology#", "foaf": "http://xmlns.com/foaf/0.1/", "wgs84_pos": "http://www.w3.org/2003/01/geo/wgs84_pos#", "wdt": "http://www.wikidata.org/prop/direct/", "schema": "http://schema.org/", "rdfs": "http://www.w3.org/2000/01/rdf-schema#", "gndo": "https://d-nb.info/standards/elementset/gnd#"}

tei = "{%s}" % namespaces["tei"]
xml = "{%s}" % namespaces["xml"]

orgr_orgs = orgr_root.xpath(".//tei:body//tei:listOrg//tei:org", namespaces=namespaces)

log = []

def get_data_from_gnd(org):
    if org.xpath("./tei:idno[@type='gnd']", namespaces=namespaces):
        if not org.xpath("./@checkedFor", namespaces=namespaces):
            org.attrib["checkedFor"] = ""
        if "gnd" not in org.attrib["checkedFor"]:
            data_dict = {}
            gnd_id = org.xpath("./tei:idno[@type='gnd']", namespaces=namespaces)[0].text
            r = requests.get(f"https://d-nb.info/gnd/{gnd_id}/about/lds.rdf")
            time.sleep(1)
            gnd_tree_root = etree.fromstring(r.content)

            # Wikidata
            if gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces):
                data_dict['wikidata_id'] = gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces)[0].split("/")[-1]
            # VIAF
            if gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'viaf')]", namespaces=namespaces):
                data_dict['viaf_id'] = gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'viaf')]", namespaces=namespaces)[0].split("/")[-1]
            # Name
            if gnd_tree_root.xpath("./rdf:Description/gndo:preferredNameForTheCorporateBody", namespaces=namespaces):
                data_dict['name'] = gnd_tree_root.xpath("./rdf:Description/gndo:preferredNameForTheCorporateBody", namespaces=namespaces)[0].text

            org.attrib["checkedFor"] += " gnd"
            org.attrib["checkedFor"] =  org.attrib["checkedFor"].strip()
            fill_register("gnd", data_dict, org)


def get_data_from_wikidata(org):
    if org.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces):
        if not org.xpath("./@checkedFor", namespaces=namespaces):
            org.attrib["checkedFor"] = ""
        if "wikidata" not in org.attrib["checkedFor"]:
            data_dict = {}
            wikidata_id = org.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces)[0].text
            r = requests.get(f" https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.rdf?flavor=dump")
            time.sleep(1)
            wikidata_tree_root = etree.fromstring(r.content)

            # GND
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P227", namespaces=namespaces):
                data_dict['gnd_id'] = wikidata_tree_root.xpath("./rdf:Description/wdt:P227", namespaces=namespaces)[0].text
            # VIAF
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P214", namespaces=namespaces):
                data_dict['viaf_id'] = wikidata_tree_root.xpath("./rdf:Description/wdt:P214", namespaces=namespaces)[0].text
            # Name
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='de']", namespaces=namespaces):
                data_dict['name'] = wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='de']", namespaces=namespaces)[0].text
            
            org.attrib["checkedFor"] += " wikidata"
            org.attrib["checkedFor"] =  org.attrib["checkedFor"].strip()
            fill_register("wikidata", data_dict, org)

def fill_register(source, data_dict, org):
    xml_id = org.xpath("./@xml:id", namespaces=namespaces)

    # Wikidata:
    if "wikidata_id" in data_dict:
        if not org.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces):
            new_element_idno = etree.SubElement(org, tei+"idno", attrib={"type": "wikidata"})
            new_element_idno.text = data_dict["wikidata_id"]
        else:
            existing_idno = org.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["wikidata_id"]:
                log.append(f"{xml_id}: Wikidata-ID ({data_dict['wikidata_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # VIAF:
    if "viaf_id" in data_dict:
        if not org.xpath("./tei:idno[@type='viaf']", namespaces=namespaces):
            new_element_idno = etree.SubElement(org, tei+"idno", attrib={"type": "viaf"})
            new_element_idno.text = data_dict["viaf_id"]
        else:
            existing_idno = org.xpath("./tei:idno[@type='viaf']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["viaf_id"]:
                log.append(f"{xml_id}: VIAF-ID ({data_dict['viaf_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # GND:
    if "gnd_id" in data_dict:
        if not org.xpath("./tei:idno[@type='gnd']", namespaces=namespaces):
            new_element_idno = etree.SubElement(org, tei+"idno", attrib={"type": "gnd"})
            new_element_idno.text = data_dict["gnd_id"]
        else:
            existing_idno = org.xpath("./tei:idno[@type='gnd']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["gnd_id"]:
                log.append(f"{xml_id}: GND-ID ({data_dict['gnd_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # Name:
    if "name" in data_dict:
        if not org.xpath("./tei:orgName", namespaces=namespaces) or org.xpath("./tei:orgName/tei:name[@source='catalog']", namespaces=namespaces):
            if not org.xpath("./tei:orgName", namespaces=namespaces): 
                new_elem_orgName = etree.Element(tei+"orgName")
                etree.SubElement(new_elem_orgName, tei+"name", attrib={"source": source})
                org.insert(0, new_elem_orgName)
            org.xpath("./tei:orgName/tei:name", namespaces=namespaces)[0].text = data_dict["name"]
            org.xpath("./tei:orgName/tei:name", namespaces=namespaces)[0].attrib['source'] = source   

def execute():
    print(">>>>>> Checking Organisations...")
    for i, org in enumerate(orgr_orgs):
        print(f"[{i}/{len(orgr_orgs)}]", org.xpath("./@xml:id", namespaces=namespaces))
        get_data_from_gnd(org)
        get_data_from_wikidata(org)

    orgr_tree.write("XML/Register/register_organisationen.xml", encoding="utf-8", pretty_print=True)

    open("Scripts/MetadatenAbgreifen/logs/organisationen_log.txt", "a", encoding="utf-8").write("\n".join(log))
    print("@@@@ organisationen.py DONE @@@@")
    if log:
        print(f"{len(log)} WARNINGS IN LOG")
    else:
        print("LOG CLEAN")
    print("___________")

execute()