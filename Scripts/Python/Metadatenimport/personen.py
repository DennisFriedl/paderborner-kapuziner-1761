# Importiert Daten aus verknüpften Datenbanken für Personen


from lxml import etree
import requests
import time

import orte
import organisationen

parser = etree.XMLParser(remove_blank_text=False)

pr_xml_text = open("XML/Register/register_personen.xml", "r", encoding="utf-8")
pr_tree = etree.parse(pr_xml_text, parser)
pr_root = pr_tree.getroot()

or_xml_text = open("XML/Register/register_orte.xml", "r", encoding="utf-8")
or_tree = etree.parse(or_xml_text, parser)
or_root = or_tree.getroot()

orgr_xml_text = open("XML/Register/register_organisationen.xml", "r", encoding="utf-8")
orgr_tree = etree.parse(orgr_xml_text, parser)
orgr_root = orgr_tree.getroot()

namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace", "owl": "http://www.w3.org/2002/07/owl#", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "gn": "http://www.geonames.org/ontology#", "foaf": "http://xmlns.com/foaf/0.1/", "wdt": "http://www.wikidata.org/prop/direct/", "schema": "http://schema.org/", "gndo": "https://d-nb.info/standards/elementset/gnd#", "rdfs": "http://www.w3.org/2000/01/rdf-schema#" ,"wgs84_pos": "http://www.w3.org/2003/01/geo/wgs84_pos#"}

tei = "{%s}" % namespaces["tei"]
xml = "{%s}" % namespaces["xml"]

pr_persons = pr_root.xpath(".//tei:body//tei:listPerson//tei:person", namespaces=namespaces)

log = []

person_order = ["idno", "affiliation", "faith", "death", "birth", "sex", "persName"] # gespiegelte Reihenfolge der Elemente in <person>
new_places_counter = 0 # Zählt, wie viele neue Orte angelegt werden mussten
new_organisations_counter = 0 # Zählt, wie viele neue Organisationen angelegt werden mussten

# Wikipedia
# Wikidata
# VIAF
# Name
# Geburtsjahr 
# Sterbejahr 
# Geburtsort (Hier muss ich ggf. auch neue Orte anlegen)
# Sterbeort
# Orden
# gender
# religion or worldview (aus Wikidata, hier den deutschen Namen der Worldview)
# In Log schreiben, wenn z.B. Daten aus GND und Wikidata nicht übereinstimmen.

def get_data_from_gnd(person):
    if person.xpath("./tei:idno[@type='gnd']", namespaces=namespaces):
        xml_id = person.xpath("./@xml:id", namespaces=namespaces)
        if not person.xpath("./@checkedFor", namespaces=namespaces):
            person.attrib["checkedFor"] = ""
        if "gnd" not in person.attrib["checkedFor"]:
            data_dict = {}
            gnd_id = person.xpath("./tei:idno[@type='gnd']", namespaces=namespaces)[0].text
            r = requests.get(f"https://d-nb.info/gnd/{gnd_id}/about/lds.rdf")
            time.sleep(1)
            gnd_tree_root = etree.fromstring(r.content)

            # Wikipedia URL
            if gnd_tree_root.xpath("./rdf:Description/foaf:page/@rdf:resource[contains(., 'wikipedia')]", namespaces=namespaces):
                data_dict['wikipedia_url'] = gnd_tree_root.xpath("./rdf:Description/foaf:page/@rdf:resource[contains(., 'wikipedia')]", namespaces=namespaces)[0]  
            # Viaf ID
            if gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'viaf')]", namespaces=namespaces):
                data_dict['viaf_id'] = gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'viaf')]", namespaces=namespaces)[0].split("/")[-1]
            # Wikidata ID
            if gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces):
                data_dict['wikidata_id'] = gnd_tree_root.xpath("./rdf:Description/owl:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces)[0].split("/")[-1]
            
            # Name
            fullname = ""
            for part in gnd_tree_root.xpath("./rdf:Description/gndo:preferredNameEntityForThePerson/rdf:Description/*", namespaces=namespaces):
                fullname += part.text + " "
            fullname = fullname.strip()
            if fullname:
                data_dict['name'] = fullname

            # Geburtsjahr
            if gnd_tree_root.xpath("./rdf:Description/gndo:dateOfBirth", namespaces=namespaces):
                elem = gnd_tree_root.xpath("./rdf:Description/gndo:dateOfBirth", namespaces=namespaces)[0]
                if elem.xpath("./@rdf:datatype='http://www.w3.org/2001/XMLSchema#gYear'", namespaces=namespaces):
                    data_dict['date_of_birth'] = elem.text
                elif elem.xpath("./@rdf:datatype='http://www.w3.org/2001/XMLSchema#date'", namespaces=namespaces):
                    date_splitted = elem.text.split("-")
                    if date_splitted[0] == "-": # Falls vorchristlich das genaue Datum bekannt ist.
                        data_dict['date_of_birth'] = date_splitted[0] + date_splitted[1]
                    else:
                        data_dict['date_of_birth'] = date_splitted[0]

            #Todesjahr
            if gnd_tree_root.xpath("./rdf:Description/gndo:dateOfDeath", namespaces=namespaces):
                elem = gnd_tree_root.xpath("./rdf:Description/gndo:dateOfDeath", namespaces=namespaces)[0]
                if elem.xpath("./@rdf:datatype='http://www.w3.org/2001/XMLSchema#gYear'", namespaces=namespaces):
                    data_dict['date_of_death'] = elem.text
                elif elem.xpath("./@rdf:datatype='http://www.w3.org/2001/XMLSchema#date'", namespaces=namespaces):
                    date_splitted = elem.text.split("-")
                    if date_splitted[0] == "-": # Falls vorchristlich das genaue Datum bekannt ist.
                        data_dict['date_of_death'] = date_splitted[0] + date_splitted[1]
                    else:
                        data_dict['date_of_death'] = date_splitted[0]
                
            # Geburtsort
            if gnd_tree_root.xpath("./rdf:Description/gndo:placeOfBirth", namespaces=namespaces):
                data_dict['place_of_birth'] = {"type": "gnd", "value": gnd_tree_root.xpath("./rdf:Description/gndo:placeOfBirth/@rdf:resource", namespaces=namespaces)[0].split("/")[-1]}
            elif gnd_tree_root.xpath("./rdf:Description/gndo:placeOfBirthAsLiteral", namespaces=namespaces):
                data_dict['place_of_birth'] = {"type": "text", "value": gnd_tree_root.xpath("./rdf:Description/gndo:placeOfBirthAsLiteral", namespaces=namespaces)[0].text}

            # Todesort
            if gnd_tree_root.xpath("./rdf:Description/gndo:placeOfDeath", namespaces=namespaces):
                data_dict['place_of_death'] = {"type": "gnd", "value": gnd_tree_root.xpath("./rdf:Description/gndo:placeOfDeath/@rdf:resource", namespaces=namespaces)[0].split("/")[-1]}
            elif gnd_tree_root.xpath("./rdf:Description/gndo:placeOfDeathAsLiteral", namespaces=namespaces):
                data_dict['place_of_death'] = {"type": "text", "value": gnd_tree_root.xpath("./rdf:Description/gndo:placeOfDeathAsLiteral", namespaces=namespaces)[0].text}
            
            # Geschlecht
            if gnd_tree_root.xpath("./rdf:Description/gndo:gender", namespaces=namespaces):
                sex = gnd_tree_root.xpath("./rdf:Description/gndo:gender/@rdf:resource", namespaces=namespaces)[0].split("#")[-1]
                if sex == "male":
                    data_dict['sex'] = "m"
                elif sex == "female":
                    data_dict['sex'] = "w"

            # Organisationen
            if gnd_tree_root.xpath("./rdf:Description/gndo:affiliation", namespaces=namespaces):
                data_dict['organisations'] = []
                for org in gnd_tree_root.xpath("./rdf:Description/gndo:affiliation/@rdf:resource", namespaces=namespaces):
                    data_dict['organisations'].append({"type": "gnd", "value": org.split("/")[-1]})            

                
            person.attrib["checkedFor"] += " gnd"
            person.attrib["checkedFor"] =  person.attrib["checkedFor"].strip()
            fill_register("gnd", data_dict)

def get_data_from_wikidata(person):
    if person.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces):
        xml_id = person.xpath("./@xml:id", namespaces=namespaces)
        if not person.xpath("./@checkedFor", namespaces=namespaces):
            person.attrib["checkedFor"] = ""
        if "wikidata" not in person.attrib["checkedFor"]:
            data_dict = {}
            wikidata_id = person.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces)[0].text
            r = requests.get(f" https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.rdf?flavor=dump")
            time.sleep(1)
            wikidata_tree_root = etree.fromstring(r.content)

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

            # Name
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='de']", namespaces=namespaces):
                data_dict['name'] = wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='de']", namespaces=namespaces)[0].text
            elif wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='en']", namespaces=namespaces):
                data_dict['name'] = wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/rdfs:label[@xml:lang='en']", namespaces=namespaces)[0].text

            # Geschlecht
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P21", namespaces=namespaces):
                sex = wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P21/@rdf:resource", namespaces=namespaces)[0].split("/")[-1]
                if sex == "Q6581097":
                    data_dict['sex'] = "m"
                elif sex == "Q6581072":
                    data_dict['sex'] = "w"

            # Geburtsjahr
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P569", namespaces=namespaces) and wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P569", namespaces=namespaces)[0].text:
                elem = wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P569", namespaces=namespaces)[0]
                date_splitted = elem.text.split("-")
                if date_splitted[0] == "": # Falls vorchristlich
                    data_dict['date_of_birth'] = "-" + date_splitted[1]
                else:
                    data_dict['date_of_birth'] = date_splitted[0]

            # Todesjahr
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P570", namespaces=namespaces) and wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P570", namespaces=namespaces)[0].text:
                elem = wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P570", namespaces=namespaces)[0]
                date_splitted = elem.text.split("-")
                if date_splitted[0] == "": # Falls vorchristlich
                    data_dict['date_of_death'] = "-" + date_splitted[1]
                else:
                    data_dict['date_of_death'] = date_splitted[0]

            # Geburtsort
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P19/@rdf:resource", namespaces=namespaces):
                data_dict['place_of_birth'] = {"type": "wikidata", "value": wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P19/@rdf:resource", namespaces=namespaces)[0].split("/")[-1]}

            # Todesort
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P20/@rdf:resource", namespaces=namespaces):
                data_dict['place_of_death'] = {"type": "wikidata", "value": wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P20/@rdf:resource", namespaces=namespaces)[0].split("/")[-1]}

            # Organisationen (spezifisch: religious order)
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P611", namespaces=namespaces):
                data_dict['organisations'] = []
                for org in wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P611/@rdf:resource", namespaces=namespaces):
                    data_dict['organisations'].append({"type": "wikidata", "value": org.split("/")[-1]})            

            # religion or worldview 
            if wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P140", namespaces=namespaces):
                data_dict['religions'] = []
                for religion in wikidata_tree_root.xpath(f"./rdf:Description[@rdf:about='http://www.wikidata.org/entity/{wikidata_id}']/wdt:P140/@rdf:resource", namespaces=namespaces):
                    data_dict['religions'].append({"type": "wikidata", "value": religion.split("/")[-1]})            


            person.attrib["checkedFor"] += " wikidata"
            person.attrib["checkedFor"] =  person.attrib["checkedFor"].strip()
            fill_register("wikidata", data_dict)


def get_data_from_viaf(person):
    if person.xpath("./tei:idno[@type='viaf']", namespaces=namespaces):
        xml_id = person.xpath("./@xml:id", namespaces=namespaces)
        if not person.xpath("./@checkedFor", namespaces=namespaces):
            person.attrib["checkedFor"] = ""
        if "viaf" not in person.attrib["checkedFor"]:
            data_dict = {}
            viaf_id = person.xpath("./tei:idno[@type='viaf']", namespaces=namespaces)[0].text
            r = requests.get(f"https://viaf.org/viaf/{viaf_id}/rdf.xml")
            time.sleep(1)
            viaf_tree_root = etree.fromstring(r.content)

            # GND
            if viaf_tree_root.xpath(f"./rdf:Description[@rdf:about='http://viaf.org/viaf/{viaf_id}']/schema:sameAs/@rdf:resource[contains(., 'd-nb.info/gnd')]", namespaces=namespaces):
                data_dict['gnd_id'] = viaf_tree_root.xpath(f"./rdf:Description[@rdf:about='http://viaf.org/viaf/{viaf_id}']/schema:sameAs/@rdf:resource[contains(., 'd-nb.info/gnd')]", namespaces=namespaces)[0].split("/")[-1]

            # Wikidata
            if viaf_tree_root.xpath(f"./rdf:Description[@rdf:about='http://viaf.org/viaf/{viaf_id}']/schema:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces):
                data_dict['wikidata_id'] = viaf_tree_root.xpath(f"./rdf:Description[@rdf:about='http://viaf.org/viaf/{viaf_id}']/schema:sameAs/@rdf:resource[contains(., 'wikidata')]", namespaces=namespaces)[0].split("/")[-1]


            person.attrib["checkedFor"] += " viaf"
            person.attrib["checkedFor"] =  person.attrib["checkedFor"].strip()
            fill_register("viaf", data_dict)



def fill_register(source, data_dict):
    global new_places_counter
    global new_organisations_counter
    xml_id = person.xpath("./@xml:id", namespaces=namespaces)

    # GND:
    if "gnd_id" in data_dict:
        if not person.xpath("./tei:idno[@type='gnd']", namespaces=namespaces):
            new_element_idno = etree.SubElement(person, tei+"idno", attrib={"type": "gnd"})
            new_element_idno.text = data_dict["gnd_id"]
        else:
            existing_idno = person.xpath("./tei:idno[@type='gnd']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["gnd_id"]:
                log.append(f"{xml_id}: GND-ID ({data_dict['gnd_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # Wikipedia
    if "wikipedia_url" in data_dict:
        if not person.xpath("./tei:idno[@type='wikipedia']", namespaces=namespaces):
            new_element_idno = etree.SubElement(person, tei+"idno", attrib={"type": "wikipedia"})
            new_element_idno.text = data_dict["wikipedia_url"]
        else:
            existing_idno = person.xpath("./tei:idno[@type='wikipedia']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["wikipedia_url"]:
                log.append(f"{xml_id}: Wikipedia-URL ({data_dict['wikipedia_url']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")
    # Wikidata
    if "wikidata_id" in data_dict:
        if not person.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces):
            new_element_idno = etree.SubElement(person, tei+"idno", attrib={"type": "wikidata"})
            new_element_idno.text = data_dict["wikidata_id"]
        else:
            existing_idno = person.xpath("./tei:idno[@type='wikidata']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["wikidata_id"]:
                log.append(f"{xml_id}: Wikidata-ID ({data_dict['wikidata_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")
    # VIAF
    if "viaf_id" in data_dict:
        if not person.xpath("./tei:idno[@type='viaf']", namespaces=namespaces):
            new_element_idno = etree.SubElement(person, tei+"idno", attrib={"type": "viaf"})
            new_element_idno.text = data_dict["viaf_id"]
        else:
            existing_idno = person.xpath("./tei:idno[@type='viaf']", namespaces=namespaces)[0].text       
            if existing_idno != data_dict["viaf_id"]:
                log.append(f"{xml_id}: VIAF-ID ({data_dict['viaf_id']}) aus {source} stimmt nicht mit vorhandener ({existing_idno}) überein.")

    # Name
    if "name" in data_dict:
        if not person.xpath("./tei:persName", namespaces=namespaces) or person.xpath("./tei:persName/tei:name[@source='catalog']", namespaces=namespaces):
            if not person.xpath("./tei:persName", namespaces=namespaces): 
                new_elem_persName = etree.Element(tei+"persName")
                etree.SubElement(new_elem_persName, tei+"name", attrib={"source": source})
                person.insert(0, new_elem_persName)
            person.xpath("./tei:persName/tei:name", namespaces=namespaces)[0].text = data_dict["name"]
            person.xpath("./tei:persName/tei:name", namespaces=namespaces)[0].attrib['source'] = source   

    # Geburt
    if "date_of_birth" in data_dict or "place_of_birth" in data_dict:
        if person.xpath("./tei:birth", namespaces=namespaces):
            birth_elem = person.xpath("./tei:birth", namespaces=namespaces)[0]
        else:
            # <birth> anlegen
            birth_elem = etree.Element(tei+"birth")
            for i in range(person_order.index("birth")+1, len(person_order)): # Findet heraus, wo er das Element anhängen muss
                if person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces):
                    person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces)[-1].addnext(birth_elem)
                    break   
    # Geburtsjahr
    if "date_of_birth" in data_dict:
        if not birth_elem.xpath("./tei:date", namespaces=namespaces):
            # <date> in <birth> anlegen
            new_element_date = etree.Element(tei+"date", attrib={"when-iso": data_dict['date_of_birth'], "source": source})
            birth_elem.insert(0, new_element_date)
        else:
            existing_date = birth_elem.xpath("./tei:date/@when-iso", namespaces=namespaces)[0]
            existing_source = birth_elem.xpath("./tei:date/@source", namespaces=namespaces)[0]
            if existing_date != data_dict["date_of_birth"]:
                log.append(f"{xml_id}: Geburtsdatum ({data_dict['date_of_birth']}) aus {source} stimmt nicht mit vorhandenem ({existing_date}) aus {existing_source} überein.")
            elif source not in existing_source:
                birth_elem.xpath("./tei:date", namespaces=namespaces)[0].attrib["source"] += " " + source
    # Geburtsort
    if "place_of_birth" in data_dict:
        if data_dict["place_of_birth"]["type"] == "text":
            place_id = data_dict["place_of_birth"]["value"] # Das wird einen Fehler im ODD auslösen, der mich darauf hinweist, den Ort händisch zu recherchieren und zu verbinden.
        else:
            if or_root.xpath(f".//tei:listPlace/tei:place[tei:idno[@type='{data_dict['place_of_birth']['type']}' and text()='{data_dict['place_of_birth']['value']}']]", namespaces=namespaces): # Gibt es den Ort schon im Ortsregister?
                place_id = or_root.xpath(f".//tei:listPlace/tei:place[tei:idno[@type='{data_dict['place_of_birth']['type']}' and text()='{data_dict['place_of_birth']['value']}']]/@xml:id", namespaces=namespaces)[0]
            else: # Neuer Ort muss angelegt werden
                new_places_counter += 1
                # get lowest free ID:
                for i in range(1, 99999):
                    current_id = "pl_" + ((5 - len(str(i))) * "0") + str(i)
                    if not or_root.xpath(f".//tei:place[@xml:id='{current_id}']", namespaces=namespaces):
                        place_id = current_id
                        break
                # neuen Ort anlegen:
                new_element_place = etree.SubElement(or_root.xpath(".//tei:listPlace", namespaces=namespaces)[0], tei+"place", attrib={xml+"id": place_id})
                new_element_idno = etree.SubElement(new_element_place, tei+"idno", attrib={"type": data_dict['place_of_birth']['type']})
                new_element_idno.text = data_dict['place_of_birth']['value']
                # neuen Ort mit Metadaten versehen:
                for i in range(2):
                    orte.get_data_from_gnd(new_element_place)
                    orte.get_data_from_wikidata(new_element_place)
                    orte.get_data_from_geonames(new_element_place)
                    orte.get_data_from_viaf(new_element_place)



        # Füllen von <placeName>        
        if not birth_elem.xpath("./tei:placeName", namespaces=namespaces):
            # <placeName> in <birth> anlegen
            etree.SubElement(birth_elem, tei+"placeName", attrib={"key": place_id, "source": source})
        else:
            existing_place_id = birth_elem.xpath("./tei:placeName/@key", namespaces=namespaces)[0]
            existing_source = birth_elem.xpath("./tei:placeName/@source", namespaces=namespaces)[0]
            if existing_place_id != place_id:
                log.append(f"{xml_id}: Geburtsort ({place_id}) aus {source} stimmt nicht mit vorhandenem ({existing_place_id}) aus {existing_source} überein.")
            elif source not in existing_source:
                birth_elem.xpath("./tei:placeName", namespaces=namespaces)[0].attrib["source"] += " " + source

    # Tod
    if "date_of_death" in data_dict or "place_of_death" in data_dict:
        if person.xpath("./tei:death", namespaces=namespaces):
            death_elem = person.xpath("./tei:death", namespaces=namespaces)[0]
        else:
            # <death> anlegen
            death_elem = etree.Element(tei+"death")
            for i in range(person_order.index("death")+1, len(person_order)): # Findet heraus, wo er das Element anhängen muss
                if person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces):
                    person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces)[-1].addnext(death_elem)
                    break  
    # Todesjahr
    if "date_of_death" in data_dict:
        if not death_elem.xpath("./tei:date", namespaces=namespaces):
            # Anlegen
            new_element_date = etree.Element(tei+"date", attrib={"when-iso": data_dict['date_of_death'], "source": source})
            death_elem.insert(0, new_element_date)
        else:
            existing_date = death_elem.xpath("./tei:date/@when-iso", namespaces=namespaces)[0]
            existing_source = death_elem.xpath("./tei:date/@source", namespaces=namespaces)[0]
            if existing_date != data_dict["date_of_death"]:
                log.append(f"{xml_id}: Todesdatum ({data_dict['date_of_death']}) aus {source} stimmt nicht mit vorhandenem ({existing_date}) aus {existing_source} überein.")
            elif source not in existing_source:
                death_elem.xpath("./tei:date", namespaces=namespaces)[0].attrib["source"] += " " + source
    # Todesort
    if "place_of_death" in data_dict:
        if data_dict["place_of_death"]["type"] == "text":
            place_id = data_dict["place_of_death"]["value"] # Das wird einen Fehler im ODD auslösen, der mich darauf hinweist, den Ort händisch zu recherchieren und zu verbinden.
        else:
            if or_root.xpath(f".//tei:listPlace/tei:place[tei:idno[@type='{data_dict['place_of_death']['type']}' and text()='{data_dict['place_of_death']['value']}']]", namespaces=namespaces): # Gibt es den Ort schon im Ortsregister?
                place_id = or_root.xpath(f".//tei:listPlace/tei:place[tei:idno[@type='{data_dict['place_of_death']['type']}' and text()='{data_dict['place_of_death']['value']}']]/@xml:id", namespaces=namespaces)[0]
            else: # Neuer Ort muss angelegt werden
                new_places_counter += 1
                # get lowest free ID:
                for i in range(1, 99999):
                    current_id = "pl_" + ((5 - len(str(i))) * "0") + str(i)
                    if not or_root.xpath(f".//tei:place[@xml:id='{current_id}']", namespaces=namespaces):
                        place_id = current_id
                        break
                # neuen Ort anlegen:
                new_element_place = etree.SubElement(or_root.xpath(".//tei:listPlace", namespaces=namespaces)[0], tei+"place", attrib={xml+"id": place_id})
                new_element_idno = etree.SubElement(new_element_place, tei+"idno", attrib={"type": data_dict['place_of_death']['type']})
                new_element_idno.text = data_dict['place_of_death']['value']
                # neuen Ort mit Metadaten versehen:
                for i in range(2):
                    orte.get_data_from_gnd(new_element_place)
                    orte.get_data_from_wikidata(new_element_place)
                    orte.get_data_from_geonames(new_element_place)
                    orte.get_data_from_viaf(new_element_place)
        # Füllen von <placeName>        
        if not death_elem.xpath("./tei:placeName", namespaces=namespaces):
            # <placeName> in <death> anlegen
            etree.SubElement(death_elem, tei+"placeName", attrib={"key": place_id, "source": source})
        else:
            existing_place_id = death_elem.xpath("./tei:placeName/@key", namespaces=namespaces)[0]
            existing_source = death_elem.xpath("./tei:placeName/@source", namespaces=namespaces)[0]
            if existing_place_id != place_id:
                log.append(f"{xml_id}: Todesort ({place_id}) aus {source} stimmt nicht mit vorhandenem ({existing_place_id}) aus {existing_source} überein.")
            elif source not in existing_source:
                death_elem.xpath("./tei:placeName", namespaces=namespaces)[0].attrib["source"] += " " + source

    # Geschlecht
    if "sex" in data_dict:
        if not person.xpath("./tei:sex", namespaces=namespaces): # neues <sex> muss angelegt werden
            sex_elem = etree.Element(tei+"sex", attrib={"value": data_dict["sex"], "source": source})
            for i in range(person_order.index("sex")+1, len(person_order)): # Findet heraus, wo er das Element anhängen muss
                if person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces):
                    person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces)[-1].addnext(sex_elem)
                    break
        else:
            existing_sex = person.xpath("./tei:sex/@value", namespaces=namespaces)[0]
            existing_source = person.xpath("./tei:sex/@source", namespaces=namespaces)[0]
            if existing_sex != data_dict["sex"]:
                log.append(f"{xml_id}: Geschlecht ({data_dict['sex']}) aus {source} stimmt nicht mit vorhandenem ({existing_sex}) aus {existing_source} überein.")
            elif source not in existing_source:
                person.xpath("./tei:sex", namespaces=namespaces)[0].attrib["source"] += " " + source
    
    # Organisationen // Achtung: Können mehrere sein!
    if "organisations" in data_dict:
        # Gibt es <affiliation> schon?
        if person.xpath("./tei:affiliation", namespaces=namespaces):
            affiliation_elem = person.xpath("./tei:affiliation", namespaces=namespaces)[0]
        else:
            # <affiliation> anlegen
            affiliation_elem = etree.Element(tei+"affiliation")
            for i in range(person_order.index("affiliation")+1, len(person_order)): # Findet heraus, wo er das Element anhängen muss
                if person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces):
                    person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces)[-1].addnext(affiliation_elem)
                    break
        for org in data_dict['organisations']:
            # Gibt es die Organisation schon im Organisationsregister?            
            if orgr_root.xpath(f".//tei:listOrg/tei:org[tei:idno[@type='{org['type']}' and text()='{org['value']}']]", namespaces=namespaces):
                org_id = orgr_root.xpath(f".//tei:listOrg/tei:org[tei:idno[@type='{org['type']}' and text()='{org['value']}']]/@xml:id", namespaces=namespaces)[0]
            else: # Neue Organisation muss angelegt werden
                new_organisations_counter += 1
                # get lowest free ID:
                for i in range(1, 99999):
                    current_id = "org_" + ((5 - len(str(i))) * "0") + str(i)
                    if not orgr_root.xpath(f".//tei:org[@xml:id='{current_id}']", namespaces=namespaces):
                        org_id = current_id
                        break
                # neue Organisation anlegen:
                new_element_org = etree.SubElement(orgr_root.xpath(".//tei:listOrg", namespaces=namespaces)[0], tei+"org", attrib={xml+"id": org_id})
                new_element_idno = etree.SubElement(new_element_org, tei+"idno", attrib={"type": org['type']})
                new_element_idno.text = org['value']
                # neue Organisation mit Metadaten versehen:
                for i in range(2):
                    organisationen.get_data_from_gnd(new_element_org)
                    organisationen.get_data_from_wikidata(new_element_org)
            # Füllen von <orgName>        
            if not affiliation_elem.xpath(f"./tei:orgName[@key='{org_id}']", namespaces=namespaces):
                # <orgName> in <affiliation> anlegen
                etree.SubElement(affiliation_elem, tei+"orgName", attrib={"key": org_id, "source": source})
            elif source not in affiliation_elem.xpath(f"./tei:orgName[@key='{org_id}']/@source", namespaces=namespaces)[0]:
                 affiliation_elem.xpath(f"./tei:orgName[@key='{org_id}']", namespaces=namespaces)[0].attrib["source"] += " " + source
    
    if "religions" in data_dict:
        for religion in data_dict['religions']:
            if not person.xpath(f"./tei:faith[text()='{religion['value']}']", namespaces=namespaces):
                new_element_faith = etree.Element(tei+"faith", attrib={"source": source})
                new_element_faith.text = religion['value']
                for i in range(person_order.index("faith")+1, len(person_order)): # Findet heraus, wo er das Element anhängen muss
                    if person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces):
                        person.xpath(f"./tei:{person_order[i]}", namespaces=namespaces)[-1].addnext(new_element_faith)
                        break

        
      
print(">>>>>> Checking Persons...")
for i, person in enumerate(pr_persons):
    print(f"[{i}/{len(pr_persons)}]", person.xpath("./@xml:id", namespaces=namespaces))
    get_data_from_gnd(person)
    get_data_from_wikidata(person)
    get_data_from_viaf(person)

pr_tree.write("XML/Register/register_personen.xml", encoding="utf-8", pretty_print=True)
or_tree.write("XML/Register/register_orte.xml", encoding="utf-8", pretty_print=True)
orgr_tree.write("XML/Register/register_organisationen.xml", encoding="utf-8", pretty_print=True)

open("Scripts/MetadatenAbgreifen/logs/personen_log.txt", "a", encoding="utf-8").write("\n".join(log))
print("@@@@ personen.py DONE @@@@")
if log:
    print(f"{len(log)} WARNINGS IN LOG")
else:
    print("LOG CLEAN")
if new_places_counter > 0:
    print(new_places_counter, "new Places, please execute orte.py!")
if new_organisations_counter > 0:
    print(new_organisations_counter, "new Organisations, please execute organisationen.py!")
print("___________")
