# Importiert Daten aus verknüpften Datenbanken für Orte

from lxml import etree
import requests
import time

parser = etree.XMLParser(remove_blank_text=False)

or_xml_text = open("XML/Register/register_orte.xml", "r", encoding="utf-8")
or_tree = etree.parse(or_xml_text, parser)
or_root = or_tree.getroot()

namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace", "owl": "http://www.w3.org/2002/07/owl#", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "gn": "http://www.geonames.org/ontology#", "foaf": "http://xmlns.com/foaf/0.1/", "wgs84_pos": "http://www.w3.org/2003/01/geo/wgs84_pos#", "wdt": "http://www.wikidata.org/prop/direct/", "schema": "http://schema.org/", "rdfs": "http://www.w3.org/2000/01/rdf-schema#"}

tei = "{%s}" % namespaces["tei"]
xml = "{%s}" % namespaces["xml"]

or_places = or_root.xpath(".//tei:body//tei:listPlace//tei:place", namespaces=namespaces)

place_order = ["idno", "country", "location", "placeName"]

log = []

def get_data_from_gnd(place):
    if place.xpath("./tei:idno[@type='gnd']", namespaces=namespaces):
        if not place.xpath("./@checkedFor", namespaces=namespaces):
            place.attrib["checkedFor"] = ""
        if "gnd" not in place.attrib["checkedFor"]:
            data_dict = {}
            gnd_id = place.xpath("./tei:idno[@type='gnd']", namespaces=namespaces)[0].text
            r = requests.get(f"https://d-nb.info/gnd/{gnd_id}/about/lds.rdf")
            time.sleep(1)
            gnd_tree_root = etree.fromstring(r.content)

            # Geonames ID
            if gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'geonames')]", namespaces=namespaces):
                data_dict['geonames_id'] = gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'geonames')]", namespaces=namespaces)[0].split("/")[-1]
            # Wikipedia URL
            if gnd_tree_root.xpath("./rdf:Description/foaf:page/@rdf:resource[contains(., 'wikipedia')]", namespaces=namespaces):
                data_dict['wikipedia_url'] = gnd_tree_root.xpath("./rdf:Description/foaf:page/@rdf:resource[contains(., 'wikipedia')]", namespaces=namespaces)[0]  
            # Viaf ID
            if gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'viaf')]", namespaces=namespaces):
                data_dict['viaf_id'] = gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'viaf')]", namespaces=namespaces)[0].split("/")[-1]
            # Wikidata ID
            if gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces):
                data_dict['wikidata_id'] = gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces)[0].split("/")[-1] 

            place.attrib["checkedFor"] += " gnd"
            place.attrib["checkedFor"] =  place.attrib["checkedFor"].strip()
            fill_register("gnd", data_dict, place)

def get_data_from_wikidata(place):
    # check for:
        # Wikipedia-URL (Wenn keine deutsche, die englische)
        # Idnos: Geonames, GND, VIAF
        # Vielleicht: Name (Wenn keiner von Geonames besteht. Hier muss ich noch in Geonames ändern, dass er Wikidata überschreiben darf)
        # Vielleicht: Koordinaten (Wenn keiner von Geonames besteht. Hier muss ich noch in Geonames ändern, dass er Wikidata überschreiben darf)
    if place.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces):
        if not place.xpath("./@checkedFor", namespaces=namespaces):
            place.attrib["checkedFor"] = ""
        if "wikidata" not in place.attrib["checkedFor"]:
            data_dict = {}
            wikidata_id = place.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces)[0].text
            r = requests.get(f" https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.rdf?flavor=dump")
            time.sleep(1)
            wikidata_tree_root = etree.fromstring(r.content)

            # Geonames ID
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P1566", namespaces=namespaces):
                data_dict['geonames_id'] = wikidata_tree_root.xpath("./rdf:Description/wdt:P1566", namespaces=namespaces)[0].text
            # GND
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P227", namespaces=namespaces):
                data_dict['gnd_id'] = wikidata_tree_root.xpath("./rdf:Description/wdt:P227", namespaces=namespaces)[0].text
            # VIAF
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P214", namespaces=namespaces):
                data_dict['viaf_id'] = wikidata_tree_root.xpath("./rdf:Description/wdt:P214", namespaces=namespaces)[0].text
            # Wikipedia
            wikipedia_articles_xpath = f"./rdf:Description[rdf:type[@rdf:resource='http://schema.org/Article'] and schema:about[@rdf:resource='http://www.wikidata.org/entity/{wikidata_id}'] and contains(schema:isPartOf/@rdf:resource, 'wikipedia')]"
            if wikidata_tree_root.xpath(wikipedia_articles_xpath + "[schema:inLanguage[text()='de']]/@rdf:about", namespaces=namespaces):                
                data_dict['wikipedia_url'] = wikidata_tree_root.xpath(wikipedia_articles_xpath + "[schema:inLanguage[text()='de']]/@rdf:about", namespaces=namespaces)[0]
            else:
                if wikidata_tree_root.xpath(wikipedia_articles_xpath + "[schema:inLanguage[text()='en']]/@rdf:about", namespaces=namespaces):
                    data_dict['wikipedia_url'] = wikidata_tree_root.xpath(wikipedia_articles_xpath + "[schema:inLanguage[text()='en']]/@rdf:about", namespaces=namespaces)[0]

            # Stadtname
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='de']", namespaces=namespaces):
                data_dict['city_name'] = wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='de']", namespaces=namespaces)[0].text
            elif wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='en']", namespaces=namespaces):
                data_dict['city_name'] = wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='en']", namespaces=namespaces)[0].text

            place.attrib["checkedFor"] += " wikidata"
            place.attrib["checkedFor"] =  place.attrib["checkedFor"].strip()
            fill_register("wikidata", data_dict, place)

def get_data_from_geonames(place):
    if place.xpath("./tei:idno[@type='geonames']", namespaces=namespaces):
        if not place.xpath("./@checkedFor", namespaces=namespaces):
            place.attrib["checkedFor"] = ""
        if "geonames" not in place.attrib["checkedFor"]:
            data_dict = {}
            geonames_id = place.xpath("./tei:idno[@type='geonames']", namespaces=namespaces)[0].text
            r = requests.get(f"https://sws.geonames.org/{geonames_id}/about.rdf")
            time.sleep(1)
            geonames_tree_root = etree.fromstring(r.content)

            # Stadtname
            if geonames_tree_root.xpath(".//gn:officialName", namespaces=namespaces):
                if geonames_tree_root.xpath(".//gn:officialName[@xml:lang='de']", namespaces=namespaces):
                    data_dict['city_name'] = geonames_tree_root.xpath(".//gn:officialName[@xml:lang='de']", namespaces=namespaces)[0].text
            else:
                if geonames_tree_root.xpath(".//gn:alternateName[@xml:lang='de']", namespaces=namespaces):
                    data_dict['city_name'] = geonames_tree_root.xpath(".//gn:alternateName[@xml:lang='de']", namespaces=namespaces)[0].text
                else:
                    data_dict['city_name'] = geonames_tree_root.xpath(".//gn:name", namespaces=namespaces)[0].text

            # Koordinaten
            if geonames_tree_root.xpath(".//wgs84_pos:lat", namespaces=namespaces):
                data_dict['coordinates'] = geonames_tree_root.xpath(".//wgs84_pos:lat", namespaces=namespaces)[0].text + " " + geonames_tree_root.xpath(".//wgs84_pos:long", namespaces=namespaces)[0].text

            # Get country:
            if geonames_tree_root.xpath(".//gn:parentCountry", namespaces=namespaces):           
                country_geonames_url = geonames_tree_root.xpath(".//gn:parentCountry/@rdf:resource", namespaces=namespaces)[0]
                r = requests.get(country_geonames_url + "/about.rdf")
                time.sleep(1)
                geonames_country_tree_root = etree.fromstring(r.content)
                if geonames_country_tree_root.xpath(".//gn:officialName[@xml:lang='de']", namespaces=namespaces):
                    data_dict['country_name'] = geonames_country_tree_root.xpath(".//gn:officialName[@xml:lang='de']", namespaces=namespaces)[0].text
                else:
                    if geonames_country_tree_root.xpath(".//gn:alternateName[@xml:lang='de']", namespaces=namespaces):
                        data_dict['country_name'] = geonames_country_tree_root.xpath(".//gn:alternateName[@xml:lang='de']", namespaces=namespaces)[0].text
                    else:
                        data_dict['country_name'] = geonames_country_tree_root.xpath(".//gn:name", namespaces=namespaces)[0].text

            place.attrib["checkedFor"] += " geonames"
            place.attrib["checkedFor"] =  place.attrib["checkedFor"].strip()
            fill_register("geonames", data_dict, place)


def get_data_from_viaf(place):
    if place.xpath("./tei:idno[@type='viaf']", namespaces=namespaces):
        xml_id = place.xpath("./@xml:id", namespaces=namespaces)
        if not place.xpath("./@checkedFor", namespaces=namespaces):
            place.attrib["checkedFor"] = ""
        if "viaf" not in place.attrib["checkedFor"]:
            data_dict = {}
            viaf_id = place.xpath("./tei:idno[@type='viaf']", namespaces=namespaces)[0].text
            r = requests.get(f"https://viaf.org/viaf/{viaf_id}/rdf.xml")
            time.sleep(1)
            viaf_tree_root = etree.fromstring(r.content)

            # GND
            if viaf_tree_root.xpath(f"./rdf:Description[@rdf:about='http://viaf.org/viaf/{viaf_id}']/schema:sameAs/@rdf:resource[contains(., 'd-nb.info/gnd')]", namespaces=namespaces):
                data_dict['gnd_id'] = viaf_tree_root.xpath(f"./rdf:Description[@rdf:about='http://viaf.org/viaf/{viaf_id}']/schema:sameAs/@rdf:resource[contains(., 'd-nb.info/gnd')]", namespaces=namespaces)[0].split("/")[-1]

            # Wikidata
            if viaf_tree_root.xpath(f"./rdf:Description[@rdf:about='http://viaf.org/viaf/{viaf_id}']/schema:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces):
                data_dict['wikidata_id'] = viaf_tree_root.xpath(f"./rdf:Description[@rdf:about='http://viaf.org/viaf/{viaf_id}']/schema:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces)[0].split("/")[-1]


            place.attrib["checkedFor"] += " viaf"
            place.attrib["checkedFor"] =  place.attrib["checkedFor"].strip()
            fill_register("viaf", data_dict, place)


def fill_register(source, data_dict, place):
    xml_id = place.xpath("./@xml:id", namespaces=namespaces)

    # GND:
    if "gnd_id" in data_dict:
        if not place.xpath("./tei:idno[@type='gnd']", namespaces=namespaces):
            new_element_idno = etree.SubElement(place, tei+"idno", attrib={"type": "gnd"})
            new_element_idno.text = data_dict["gnd_id"]
        else:
            existing_idno = place.xpath("./tei:idno[@type='gnd']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["gnd_id"]:
                log.append(f"{xml_id}: GND-ID ({data_dict['gnd_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # Geonames:
    if "geonames_id" in data_dict:      
        if not place.xpath("./tei:idno[@type='geonames']", namespaces=namespaces):
            new_element_idno = etree.SubElement(place, tei+"idno", attrib={"type": "geonames"})
            new_element_idno.text = data_dict["geonames_id"]
        else:
            existing_idno = place.xpath("./tei:idno[@type='geonames']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["geonames_id"]:
                log.append(f"{xml_id}: GeoNames-ID ({data_dict['geonames_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # Wikipedia:
    if "wikipedia_url" in data_dict:
        if not place.xpath("./tei:idno[@type='wikipedia']", namespaces=namespaces):
            new_element_idno = etree.SubElement(place, tei+"idno", attrib={"type": "wikipedia"})
            new_element_idno.text = data_dict["wikipedia_url"]
        else:
            existing_idno = place.xpath("./tei:idno[@type='wikipedia']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["wikipedia_url"]:
                log.append(f"{xml_id}: Wikipedia-URL ({data_dict['wikipedia_url']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # VIAF:
    if "viaf_id" in data_dict:
        if not place.xpath("./tei:idno[@type='viaf']", namespaces=namespaces):
            new_element_idno = etree.SubElement(place, tei+"idno", attrib={"type": "viaf"})
            new_element_idno.text = data_dict["viaf_id"]
        else:
            existing_idno = place.xpath("./tei:idno[@type='viaf']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["viaf_id"]:
                log.append(f"{xml_id}: VIAF-ID ({data_dict['viaf_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # Wikidata:
    if "wikidata_id" in data_dict:
        if not place.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces):
            new_element_idno = etree.SubElement(place, tei+"idno", attrib={"type": "wikidata"})
            new_element_idno.text = data_dict["wikidata_id"]
        else:
            existing_idno = place.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["wikidata_id"]:
                log.append(f"{xml_id}: Wikidata-ID ({data_dict['wikidata_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # Stadtname:
    if "city_name" in data_dict:
        if not place.xpath("./tei:placeName", namespaces=namespaces) or place.xpath("./tei:placeName/tei:name[@source='catalog']", namespaces=namespaces):
            if not place.xpath("./tei:placeName", namespaces=namespaces): 
                new_elem_placeName = etree.Element(tei+"placeName")
                etree.SubElement(new_elem_placeName, tei+"name", attrib={"source": source})
                place.insert(0, new_elem_placeName)
            place.xpath("./tei:placeName/tei:name", namespaces=namespaces)[0].text = data_dict["city_name"]
            place.xpath("./tei:placeName/tei:name", namespaces=namespaces)[0].attrib['source'] = source   

    # Koordinaten:
    if "coordinates" in data_dict and not place.xpath("./tei:location/tei:geo", namespaces=namespaces):
        new_element_location = etree.Element(tei+"location")
        new_element_geo = etree.SubElement(new_element_location, tei+"geo", attrib={"decls": "#WGS", "source": source})
        new_element_geo.text = data_dict["coordinates"]
        for i in range(place_order.index("location")+1, len(place_order)): # Findet heraus, wo er das Element anhängen muss
                if place.xpath(f"./tei:{place_order[i]}", namespaces=namespaces):
                    place.xpath(f"./tei:{place_order[i]}", namespaces=namespaces)[-1].addnext(new_element_location)
                    break
        else: # Wenn er bis zum Ende durchläuft ohne Position zu finden, hänge an den Anfang.
            place.insert(0, new_element_location)

    # Ländername:
    if "country_name" in data_dict and not place.xpath("./tei:country", namespaces=namespaces):
        new_element_country = etree.Element(tei+"country", attrib={"source": source})
        new_element_country.text = data_dict["country_name"]
        for i in range(place_order.index("country")+1, len(place_order)): # Findet heraus, wo er das Element anhängen muss
                if place.xpath(f"./tei:{place_order[i]}", namespaces=namespaces):
                    place.xpath(f"./tei:{place_order[i]}", namespaces=namespaces)[-1].addnext(new_element_country)
                    break 
        else: # Wenn er bis zum Ende durchläuft ohne Position zu finden, hänge an den Anfang.
            place.insert(0, new_element_country)

def execute():
    print(">>>>>> Checking Places...")
    for i, place in enumerate(or_places):
        print(f"[{i}/{len(or_places)}]", place.xpath("./@xml:id", namespaces=namespaces))    
        get_data_from_wikidata(place)
        get_data_from_gnd(place)
        get_data_from_geonames(place)
        get_data_from_viaf(place)

    or_tree.write("XML/Register/register_orte.xml", encoding="utf-8", pretty_print=True)

    open("Scripts/MetadatenAbgreifen//logs/orte_log.txt", "a", encoding="utf-8").write("\n".join(log))
    print("@@@@ orte.py DONE @@@@")
    if log:
        print(f"{len(log)} WARNINGS IN LOG")
    else:
        print("LOG CLEAN")
    print("___________")

execute()

