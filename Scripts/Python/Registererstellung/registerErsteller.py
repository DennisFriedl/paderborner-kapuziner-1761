# Erstellt aus der Auszeichnung verschiedene Entitätsregister

from pydoc import resolve
from lxml import etree
from datetime import datetime
import inspect
import jellyfish

log = []
blacklist = ["Tomus 1us", "Tomus 2us", "Tomus 3us", "Tomus 4us", "Tomus 5us", "Tomus 6us", "Tomus 7us", "Tomus 8us", "Tomus 9us", "Tomus I", "Tomus II", "Tomus III", "Tomus IV", "Tomus V", "Tomus VI", "Tomus VII", "Tomus VIII", "Tomus IX", "Biblia Germanica", "Biblia Latina", "Biblia Belgica", "Biblia Germanica", "Tomus 1mus", "Tomus 2dus", "Tomus 1 mus", "Tomus 4 tus", "Tomus 2 dus", "Tomus 3 tius", "Tomus 4 tus"]

parser = etree.XMLParser(remove_blank_text=False)

az_xml_text = open("XML/Auszeichnung/kapuziner_pb.xml", "r", encoding="utf-8")
az_tree = etree.parse(az_xml_text, parser)
az_root = az_tree.getroot()

or_xml_text = open("XML/Register/register_orte.xml", "r", encoding="utf-8")
or_tree = etree.parse(or_xml_text, parser)
or_root = or_tree.getroot()

pr_xml_text = open("XML/Register/register_personen.xml", "r", encoding="utf-8")
pr_tree = etree.parse(pr_xml_text, parser)
pr_root = pr_tree.getroot()

wr_xml_text = open("XML/Register/register_werke.xml", "r", encoding="utf-8")
wr_tree = etree.parse(wr_xml_text, parser)
wr_root = wr_tree.getroot()

org_xml_text = open("XML/Register/register_organisationen.xml", "r", encoding="utf-8")
org_tree = etree.parse(org_xml_text, parser)
org_root = org_tree.getroot()

namespaces = {"tei": "http://www.tei-c.org/ns/1.0", "xml": "http://www.w3.org/XML/1998/namespace"}


print("Collecting entities...")
az_places = az_root.xpath(".//tei:body//tei:table//tei:cell//tei:placeName[not(@copyOf)]", namespaces=namespaces)
or_places = or_root.xpath(".//tei:body//tei:listPlace//tei:place", namespaces=namespaces)
az_organisations = az_root.xpath(".//tei:body//tei:table//tei:cell//tei:orgName[not(@copyOf)]", namespaces=namespaces)
org_organisations = org_root.xpath(".//tei:body//tei:listOrg//tei:org", namespaces=namespaces)
az_persons = az_root.xpath(".//tei:body//tei:table//tei:cell//tei:persName[not(@copyOf) and not(ancestor::tei:persName)]", namespaces=namespaces)
pr_persons = pr_root.xpath(".//tei:body//tei:listPerson//tei:person", namespaces=namespaces)
az_serieses = az_root.xpath(".//tei:body//tei:table//tei:cell//tei:title[@level='s' and not(@copyOf)]", namespaces=namespaces)
wr_serieses = wr_root.xpath(".//tei:body//tei:listBibl//tei:bibl[@type='s']", namespaces=namespaces)
az_monographs = az_root.xpath(".//tei:body//tei:table//tei:cell//tei:title[@level='m' and not(@copyOf)]", namespaces=namespaces)
wr_monographs = wr_root.xpath(".//tei:body//tei:listBibl//tei:bibl[@type='m']", namespaces=namespaces)
az_editions = az_root.xpath(".//tei:body//tei:table//tei:cell//tei:rs[@type='edition' and not(@copyOf)]", namespaces=namespaces)


tei = "{%s}" % namespaces["tei"]
xml = "{%s}" % namespaces["xml"]


def lineno():
    """Gibt die aktuelle Zeile im Skript zurück"""
    return inspect.currentframe().f_back.f_lineno


def resolve_text(elem):
    def rek(elem):
        whole_string = ""
        try:
            whole_string += elem.text
        except:
            pass
        for child in elem:
            if child.tag == tei+"choice":
                whole_string += child.xpath("./tei:expan", namespaces=namespaces)[0].text
                try:
                    whole_string += child.tail
                except:
                    pass
            else:
                whole_string += rek(child)
        try:
            whole_string += elem.tail
        except:
            pass
        return whole_string    
    whole_string = ""
    try:
        whole_string += elem.text
    except:
        pass
    for child in elem:
        if child.tag == tei+"choice":
            whole_string += child.xpath("./tei:expan", namespaces=namespaces)[0].text
            try:
                whole_string += child.tail
            except:
                pass
        else:
            whole_string += rek(child)

    return ' '.join(whole_string.split()).strip()


def resolve_copyOf(elem_name): # Brauch ich das überhaupt oder löst sich @copyOf erst in der Abfrage der API auf?
    print("\n>>> Resolving @copyOf...")
    az_elements = az_root.xpath(f".//tei:body//{elem_name}[@copyOf and not(@key)]", namespaces=namespaces) 
    
    for elem in az_elements:
        copyOf_value = elem.attrib['copyOf'][1:]
        key_value_list = az_root.xpath(f".//tei:body//*[@xml:id='{copyOf_value}']/@key", namespaces=namespaces)
        if key_value_list:
            key_value = key_value_list[0]
            elem.attrib["key"] = key_value
        else:
            log.append(f"Line {lineno()}: Für @copyOf-Wert von <{elem.tag}> '{resolve_text(elem)}' [Line {elem.sourceline} in Katalog] konnte kein passender @key gefunden werden.")
        

def get_new_id(list_of_ids):
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    new_list_of_ids = []
    prefix = list_of_ids[0].rsplit("_", 1)[0] + "_"
    for item in list_of_ids:
        new_list_of_ids.append(item.split("_")[-1])
    new_id_value =  max(new_list_of_ids)
    if new_id_value not in alphabet:
        new_id_value = str(int(new_id_value) + 1)
        return prefix + ("0" * (5 - len(new_id_value))) + new_id_value
    else:
        new_id_value = chr(ord(new_id_value) + 1)
        return prefix + new_id_value


def register_places():
    print("\n>>>>>> CONNECTING PLACES... <<<<<<")

    for az_place in az_places:
        treffer = 0
        similar_list = []

        if "key" not in az_place.attrib:
            for or_place in or_places:
                or_place_addNames = or_place.xpath("./tei:placeName/tei:addName[@source='catalog']", namespaces=namespaces)
                for addName in or_place_addNames:
                    if resolve_text(az_place) == resolve_text(addName):
                        treffer += 1
                        xml_id = or_place.xpath('./@xml:id')[0]
                        print(resolve_text(az_place) + " entspricht Id " + or_place.xpath('./@xml:id')[0] + " im Register")
                        az_place.attrib["key"] = xml_id
                        break
                    # Similarity:
                    elif jellyfish.jaro_similarity(resolve_text(az_place), resolve_text(addName)) > 0.77:
                        similar_list.append(f"{resolve_text(addName)} [Line {addName.sourceline}]")
                else:
                    name =  or_place.xpath("./tei:placeName/tei:name", namespaces=namespaces)[0]
                    if resolve_text(az_place) == resolve_text(name):
                        log.append(f"Line {lineno()}: <placeName> '{resolve_text(az_place)}' passt zu <name> in Line {name.sourceline}, jedoch zu keinem <addName> im gleichen Element")
                    # Similarity
                    elif jellyfish.jaro_similarity(resolve_text(az_place), resolve_text(name)) > 0.77:
                        similar_list.append(f"{resolve_text(name)} [Line {name.sourceline}]")
            if treffer > 1:
                log.append(f"Line {lineno()}: <placeName> '{resolve_text(az_place)}' [Line {az_place.sourceline} in Katalog] hatte {treffer} Treffer.")
            elif treffer == 0:
                print(resolve_text(az_place) + " ist neu")
                newID = get_new_id(or_root.xpath(".//tei:body//tei:listPlace/tei:place/@xml:id", namespaces=namespaces))
                newName = resolve_text(az_place)

                newElementPlace = etree.SubElement(or_root.xpath(".//tei:listPlace", namespaces=namespaces)[0], tei+"place", attrib={xml+"id": newID})
                newElementPlaceName = etree.SubElement(newElementPlace, tei+"placeName")
                newElementName = etree.SubElement(newElementPlaceName, tei+"name", attrib={"source": "catalog"})
                newElementName.text = newName
                newElementAddName = etree.SubElement(newElementPlaceName, tei+"addName", attrib={"source": "catalog", xml+"lang": "lat"})
                newElementAddName.text = newName

                az_place.attrib["key"] = newID

                or_places.append(newElementPlace)

                if similar_list:
                    log.append(f"Line {lineno()}: <placeName> '{resolve_text(az_place)}' ({az_place.sourceline}) nicht gefunden, doch hat Ähnlichkeit mit: {', '.join(similar_list)}")
        else:
            key = az_place.attrib['key']
            ort = or_root.xpath(f".//tei:place[@xml:id='{key}']", namespaces=namespaces)[0]
            all_addName_with_id = ort.xpath(f"./tei:placeName/tei:addName[@source='catalog']", namespaces=namespaces)
            for addName in all_addName_with_id:
                if resolve_text(az_place) == resolve_text(addName):
                    break
            else:
                log.append(f"Line {lineno()}: <placeName> '{resolve_text(az_place)}' [Line {az_place.sourceline} in Katalog] hat bereits einen @key, jedoch passt dieser nicht mit <addName> [Line {ort.sourceline} in Ortsregister] überein")

def register_organisations():
    print("\n>>>>>> CONNECTING ORGANISATIONS... <<<<<<")

    for az_organisation in az_organisations:
        treffer = 0

        if "key" not in az_organisation.attrib:
            for org_organisation in org_organisations:
                org_organisation_addNames = org_organisation.xpath("./tei:orgName/tei:addName[@source='catalog']", namespaces=namespaces)
                for addName in org_organisation_addNames:
                    if resolve_text(az_organisation) == resolve_text(addName):
                        treffer += 1
                        xml_id = org_organisation.xpath('./@xml:id')[0]
                        print(resolve_text(az_organisation) + " entspricht Id " + org_organisation.xpath('./@xml:id')[0] + " im Register")
                        az_organisation.attrib["key"] = xml_id
                        break
            if treffer > 1:
                log.append(f"Line {lineno()}: <orgName> '{resolve_text(az_organisation)}' [Line {az_organisation.sourceline} in Katalog] hatte {treffer} Treffer.")
            elif treffer == 0:
                print(resolve_text(az_organisation) + " ist neu")
                newID = get_new_id(org_root.xpath(".//tei:body//tei:listOrg/tei:org/@xml:id", namespaces=namespaces))
                newName = resolve_text(az_organisation)

                newElementOrg = etree.SubElement(org_root.xpath(".//tei:listOrg", namespaces=namespaces)[0], tei+"org", attrib={xml+"id": newID})
                newElementOrgName = etree.SubElement(newElementOrg, tei+"orgName")
                newElementName = etree.SubElement(newElementOrgName, tei+"name", attrib={"source": "catalog"})
                newElementName.text = newName
                newElementAddName = etree.SubElement(newElementOrgName, tei+"addName", attrib={"source": "catalog", xml+"lang": "lat"})
                newElementAddName.text = newName

                az_organisation.attrib["key"] = newID

                org_organisations.append(newElementOrg)

        else:
            key = az_organisation.attrib['key']
            org = org_root.xpath(f".//tei:org[@xml:id='{key}']", namespaces=namespaces)[0]
            all_addName_with_id = org.xpath(f"./tei:orgName/tei:addName[@source='catalog']", namespaces=namespaces)
            for addName in all_addName_with_id:
                if resolve_text(az_organisation) == resolve_text(addName):
                    break
            else:
                log.append(f"Line {lineno()}: <orgName> '{resolve_text(az_organisation)}' [Line {az_organisation.sourceline} in Katalog] hat bereits einen @key, jedoch passt dieser nicht mit <addName> [Line {org.sourceline} in Organisationsregister] überein")

def register_persons():
    print("\n>>>>>> CONNECTING PERSONS... <<<<<<")

    for az_person in az_persons:
        treffer = 0
        similar_list = []

        if "key" not in az_person.attrib:
            for pr_person in pr_persons:
                pr_person_addNames = pr_person.xpath("./tei:persName/tei:addName[@source='catalog']", namespaces=namespaces)
                for addName in pr_person_addNames:
                    if resolve_text(az_person) == resolve_text(addName):
                        treffer += 1
                        xml_id = pr_person.xpath('./@xml:id')[0]
                        print(resolve_text(az_person) + " entspricht Id " + pr_person.xpath('./@xml:id')[0] + " im Register")
                        az_person.attrib["key"] = xml_id
                        break
                    # Similarity:
                    elif jellyfish.jaro_similarity(resolve_text(az_person), resolve_text(addName)) > 0.82:
                        similar_list.append(f"{resolve_text(addName)} [Line {addName.sourceline}]")
                else:
                    name =  pr_person.xpath("./tei:persName/tei:name", namespaces=namespaces)[0]
                    if resolve_text(az_person) == resolve_text(name):
                        log.append(f"Line {lineno()}: <persName> '{resolve_text(az_person)}' passt zu <name> in Line {name.sourceline}, jedoch zu keinem <addName> im gleichen Element")
                    # Similarity
                    elif jellyfish.jaro_similarity(resolve_text(az_person), resolve_text(name)) > 0.82:
                        similar_list.append(f"{resolve_text(name)} [Line {name.sourceline}]")
            if treffer > 1:
                log.append(f"Line {lineno()}: <persName> '{resolve_text(az_person)}' [Line {az_person.sourceline} in Katalog] hatte {treffer} Treffer.")
            elif treffer == 0:
                print(resolve_text(az_person) + " ist neu")
                newID = get_new_id(pr_root.xpath(".//tei:body//tei:listPerson/tei:person/@xml:id", namespaces=namespaces))
                newName = resolve_text(az_person)

                newElementPerson = etree.SubElement(pr_root.xpath(".//tei:listPerson", namespaces=namespaces)[0], tei+"person", attrib={xml+"id": newID})
                newElementPersName = etree.SubElement(newElementPerson, tei+"persName")
                newElementName = etree.SubElement(newElementPersName, tei+"name", attrib={"source": "catalog"})
                newElementName.text = newName
                newElementAddName = etree.SubElement(newElementPersName, tei+"addName", attrib={"source": "catalog", xml+"lang": "lat"})
                newElementAddName.text = newName

                az_person.attrib["key"] = newID

                pr_persons.append(newElementPerson)

                if similar_list:
                    log.append(f"Line {lineno()}: <persName> '{resolve_text(az_person)}' ({az_person.sourceline}) nicht gefunden, doch hat Ähnlichkeit mit: {', '.join(similar_list)}")
        else:
            key = az_person.attrib['key']
            person = pr_root.xpath(f".//tei:person[@xml:id='{key}']", namespaces=namespaces)[0]
            all_addName_with_id = person.xpath(f"./tei:persName/tei:addName[@source='catalog']", namespaces=namespaces)
            for addName in all_addName_with_id:
                if resolve_text(az_person) == resolve_text(addName):
                    break
            else:
                log.append(f"Line {lineno()}: <persName> '{resolve_text(az_person)}' [Line {az_person.sourceline} in Katalog] hat bereits einen @key, jedoch passt dieser nicht mit <addName> [Line {person.sourceline} in Personenregister] überein")

        ## ACHTUNG: HIER KONTROLLIERT ER NOCHMAL JEDE EINZELNE PERSON, OB IM REGISTER DIE RICHTIGE ORG STEHT. Das habe ich gemacht, weil ich die Funktion der Organisationsverbindung nachträglich eingefügt habe. Das könnte man hier verbessern, dass er nur Personen überprüft, die noch keinen key haben:
        if az_person.xpath(".//tei:orgName", namespaces=namespaces):
            org_keys = az_person.xpath(".//tei:orgName/@key", namespaces=namespaces)
            for org_key in org_keys:
                if not person.xpath(f"./tei:affiliation/tei:orgName[@key='{org_key}']", namespaces=namespaces):
                    #etree.SubElement(person, tei+"orgName", attrib={"key": org_key, "source": "catalog"})
                    print(f"{person.xpath('./@xml:id', namespaces=namespaces)} is member of {org_key}")


def register_serieses():
    print("\n>>>>>> CONNECTING SERIESES... <<<<<<")

    for az_series in az_serieses:
        similar_list = []

        if "key" not in az_series.attrib:
            for wr_series in wr_serieses:
                wr_series_name_and_addNames = wr_series.xpath("./tei:title/tei:title[@type='main']", namespaces=namespaces) + wr_series.xpath("./tei:addName", namespaces=namespaces)
                for name_or_addName in wr_series_name_and_addNames:
                    if resolve_text(name_or_addName) not in blacklist:
                        if jellyfish.jaro_similarity(resolve_text(az_series), resolve_text(name_or_addName)) > 0.7:
                            similar_list.append(f"{resolve_text(name_or_addName)} [Line {name_or_addName.sourceline}]")

            print(f"Lege Serie {resolve_text(az_series)} ({az_series.sourceline}) an")
            newID = get_new_id(wr_root.xpath(".//tei:body//tei:listBibl//tei:bibl[@type='s']/@xml:id", namespaces=namespaces))
            newName = resolve_text(az_series)

            newElementBibl = etree.SubElement(wr_root.xpath(".//tei:listBibl", namespaces=namespaces)[0], tei+"bibl", attrib={xml+"id": newID, "type": "s"})
            newElementTitle = etree.SubElement(newElementBibl, tei+"title", attrib={"source": "catalog"})
            newElementTitleInTitle = etree.SubElement(newElementTitle, tei+"title", attrib={"type": "main"})
            newElementTitleInTitle.text = newName
            newElementAddName = etree.SubElement(newElementBibl, tei+"addName", attrib={"source": "catalog"})
            newElementAddName.text = newName

            az_series.attrib["key"] = newID

            wr_serieses.append(newElementBibl)

            # if similar_list:
            #     log.append(f"Line {lineno()}: Serie '{resolve_text(az_series)}' [Line {az_series.sourceline}] hat Ähnlichkeit mit: {', '.join(similar_list)}")
        
        else:
            key = az_series.attrib['key']
            serie = wr_root.xpath(f".//tei:bibl[@xml:id='{key}']", namespaces=namespaces)[0]
            all_addName_with_id = serie.xpath(f"./tei:addName[@source='catalog']", namespaces=namespaces)
            for addName in all_addName_with_id:
                if resolve_text(az_series) == resolve_text(addName):
                    break
            else:
                log.append(f"Line {lineno()}: Serie '{resolve_text(az_series)}' [Line {az_series.sourceline} in Katalog] hat bereits einen @key, jedoch passt dieser nicht mit <addName> [Line {serie.sourceline} in Werkregister] überein")

def register_monographs():
    print("\n>>>>>> CONNECTING MONOGRAPHS... <<<<<<")

    for az_monograph in az_monographs:
        similar_list = []

        if "key" not in az_monograph.attrib:
            for wr_monograph in wr_monographs:
                wr_monograph_name_and_addNames = wr_monograph.xpath("./tei:title/tei:title[@type='main']", namespaces=namespaces) + wr_monograph.xpath("./tei:addName", namespaces=namespaces)
                for name_or_addName in wr_monograph_name_and_addNames:
                    if resolve_text(name_or_addName) not in blacklist:
                        if jellyfish.jaro_similarity(resolve_text(az_monograph), resolve_text(name_or_addName)) > 0.7:
                            similar_list.append(f"{resolve_text(name_or_addName)} [Line {name_or_addName.sourceline}]")
                
            print(f"Lege Monographie {resolve_text(az_monograph)} ({az_monograph.sourceline}) an")
            newID = get_new_id(wr_root.xpath(".//tei:body//tei:listBibl//tei:bibl[@type='m']/@xml:id", namespaces=namespaces)) 
            newName = resolve_text(az_monograph)

            associated_series = az_monograph.xpath("./ancestor::tei:row//tei:title[@level='s']", namespaces=namespaces)
            if associated_series:
                associated_series = associated_series[0]
                associated_series_id = associated_series.attrib["key"]
                newElementBibl = etree.SubElement(wr_root.xpath(f".//tei:listBibl//tei:bibl[@xml:id='{associated_series_id}']", namespaces=namespaces)[0], tei+"bibl", attrib={xml+"id": newID, "type": "m"})
            else:
                newElementBibl = etree.SubElement(wr_root.xpath(f".//tei:listBibl", namespaces=namespaces)[0], tei+"bibl", attrib={xml+"id": newID, "type": "m"})
            newElementTitle = etree.SubElement(newElementBibl, tei+"title", attrib={"source": "catalog"})
            newElementTitleInTitle = etree.SubElement(newElementTitle, tei+"title", attrib={"type": "main"})
            newElementTitleInTitle.text = newName
            newElementAddName = etree.SubElement(newElementBibl, tei+"addName", attrib={"source": "catalog"})
            newElementAddName.text = newName
            if "n" in az_monograph.attrib:
                n = str(az_monograph.attrib['n'])
                newElementBiblScope = etree.SubElement(newElementBibl, tei+"biblScope", attrib={"unit": "volume", "n": n})
            author_keys = az_monograph.xpath("./ancestor::tei:row//tei:persName[@role='author']/@key", namespaces=namespaces)
            for author_key in author_keys:
                newElementAuthor = etree.SubElement(newElementBibl, tei+"author", attrib={"key": author_key, "source": "catalog"})
            newElementTextLang = etree.SubElement(newElementBibl, tei+"textLang", attrib={"mainLang": "lat", "source": "auto"})

            az_monograph.attrib["key"] = newID

            wr_monographs.append(newElementBibl)

            # if similar_list:
            #     log.append(f"Line {lineno()}: Monographie '{resolve_text(az_monograph)}' hat Ähnlichkeit mit: {', '.join(similar_list)}")
        
        else:
            if resolve_text(az_monograph):
                key = az_monograph.attrib['key']
                monograph = wr_root.xpath(f".//tei:bibl[@xml:id='{key}']", namespaces=namespaces)[0]
                all_addName_with_id = monograph.xpath(f"./tei:addName[@source='catalog']", namespaces=namespaces)
                for addName in all_addName_with_id:
                    if resolve_text(az_monograph) == resolve_text(addName):
                        break
                else:
                    log.append(f"Line {lineno()}: Monographie '{resolve_text(az_monograph)}' [Line {az_monograph.sourceline} in Katalog] hat bereits einen @key, jedoch passt dieser nicht mit <addName> [Line {monograph.sourceline} in Werkregister] überein")

def register_editions():
    print("\n>>>>>> CONNECTING EDITIONS... <<<<<<")

    for az_edition in az_editions:
        if "key" not in az_edition.attrib:
            az_associated_monograph = az_edition.xpath("./preceding-sibling::tei:title[@level='m']", namespaces=namespaces)[0]
            print(f"Lege Edition für Monographie {resolve_text(az_associated_monograph)} ({az_associated_monograph.sourceline}) an")
            associated_monograph_id = az_associated_monograph.attrib["key"]
            wr_associated_monograph = wr_root.xpath(f".//tei:body//tei:listBibl//tei:bibl[@xml:id='{associated_monograph_id}']", namespaces = namespaces)[0]           
            all_preceding_editions = wr_associated_monograph.xpath(f".//tei:edition/@xml:id", namespaces=namespaces)
            if all_preceding_editions:
                newID = get_new_id(all_preceding_editions)
            else:
                newID = associated_monograph_id + "_a"
            date = None
            try:
                date = az_edition.xpath("./ancestor::tei:row//tei:date[@type='pubDate']/@when-iso", namespaces=namespaces)[0]
            except:
                pass
            places = az_edition.xpath("./ancestor::tei:row//tei:placeName[@type='pubPlace']/@key", namespaces=namespaces)
            n = None
            try:
                n = az_edition.xpath("./ancestor::tei:row//tei:dim[@type='folio']/@n", namespaces=namespaces)[0]
            except:
                pass

            newElementEdition = etree.SubElement(wr_root.xpath(f".//tei:listBibl//tei:bibl[@xml:id='{associated_monograph_id}']", namespaces=namespaces)[0], tei+"edition", attrib={xml+"id": newID})
            if date:
                etree.SubElement(newElementEdition, tei+"date", attrib={"when-iso": date, "source": "catalog"})
            for place in places:
                etree.SubElement(newElementEdition, tei+"placeName", attrib={"key": place, "source": "catalog"})
            if n:
                newElementDimensions = etree.SubElement(newElementEdition, tei+"dimensions", attrib={"source": "catalog"})
                newElementDim = etree.SubElement(newElementDimensions, tei+"dim", attrib={"type": "folio", "n": n})

            az_edition.attrib["key"] = newID

        else:
            pass

def register_entities():
    register_places()
    resolve_copyOf("tei:placeName")
    register_organisations()
    resolve_copyOf("tei:orgName")
    register_persons()
    resolve_copyOf("tei:persName")
    register_serieses()
    resolve_copyOf("tei:title[@level='s']")
    register_monographs()
    resolve_copyOf("tei:title[@level='m']")
    register_editions()
    resolve_copyOf("tei:rs[@type='edition']")

def correct_places():
    # Aus Sicht der Auszeichnung:
    # geht alle Orte in der Auszeichnung durch und guckt, ob es schon einen addName-Eintrag im Register gibt
    print("\n>>>>>> CORRECTING PLACES (Sicht d. Auszeichnung)... <<<<<<")
    for az_place in az_places:
        key = az_place.attrib['key']
        ort = or_root.xpath(f".//tei:place[@xml:id='{key}']", namespaces=namespaces)[0]
        all_addName_with_id = ort.xpath(f"./tei:placeName/tei:addName[@source='catalog']", namespaces=namespaces)
        if resolve_text(az_place):
            for addName in all_addName_with_id:
                # Wenn gleich mit addName
                if resolve_text(az_place) == resolve_text(addName):
                    break
            else: # Wenn kein addName übereinstimmt
                # Dann lege neues addName an
                print(key + " " + resolve_text(az_place) + " nicht in addNames gefunden. Lege an...")
                newElementAddName = etree.SubElement(ort.xpath(f"./tei:placeName", namespaces=namespaces)[0], tei+"addName", attrib={"source": "catalog", xml+"lang": "lat"})
                newElementAddName.text = resolve_text(az_place)
        
    # Aus Sicht des Registers:
    # gehe alle addNames durch und gucke, ob es die in der Auszeichnung gibt.
    print("\n>>>>>> CORRECTING PLACES (Sicht d. Registers)... <<<<<<")
    for or_place in or_places:
        key = or_place.attrib[xml+'id']
        vorkommen_in_az = az_root.xpath(f".//tei:placeName[@key='{key}']", namespaces=namespaces)
        all_addName = or_place.xpath(f"./tei:placeName/tei:addName[@source='catalog']", namespaces=namespaces)
        for addName in all_addName:
            for ort_in_az in vorkommen_in_az:
                if resolve_text(addName) == resolve_text(ort_in_az): 
                    break
            else: # wenn es ihn nicht in Auszeichnung gibt
                # dann lösche addName-Eintrag im Register
                 print(f"{key} addName {resolve_text(addName)} nicht in d. Auszeichnung gefunden. Lösche...")
                 addName.getparent().remove(addName)
        # gucke, ob Name aus @catalog auch in addNames vorhanden ist, wenn nicht, übernehme ersten addNames
        if or_place.xpath("./tei:placeName/tei:name[@source='catalog']", namespaces=namespaces):
            name = or_place.xpath("./tei:placeName/tei:name[@source='catalog']", namespaces=namespaces)[0]
            if all_addName:
                for addName in all_addName:
                    if resolve_text(name) == resolve_text(addName):
                        break
                else: # wenn es ihn nicht in addNames gibt
                    # dann nehme ersten addName
                    print(f"{key} {resolve_text(name)} nicht in addNames gefunden, ersetze mit {resolve_text(all_addName[0])}...")
                    name.text = resolve_text(all_addName[0])

def correct_persons():
    # Aus Sicht der Auszeichnung:
    # geht alle Personen in der Auszeichnung durch und guckt, ob es schon einen addName-Eintrag im Register gibt
    print("\n>>>>>> CORRECTING PERSONS (Sicht d. Auszeichnung)... <<<<<<")
    for az_person in az_persons:
        key = az_person.attrib['key']
        person = pr_root.xpath(f".//tei:person[@xml:id='{key}']", namespaces=namespaces)[0]
        all_addName_with_id = person.xpath(f"./tei:persName/tei:addName[@source='catalog']", namespaces=namespaces)
        if resolve_text(az_person):
            for addName in all_addName_with_id:
                # Wenn gleich mit addName
                if resolve_text(az_person) == resolve_text(addName):
                    break
            else: # Wenn kein addName übereinstimmt
                # Dann lege neues addName an
                print(key + " " + resolve_text(az_person) + " nicht in addNames gefunden. Lege an...")
                newElementAddName = etree.SubElement(person.xpath(f"./tei:persName", namespaces=namespaces)[0], tei+"addName", attrib={"source": "catalog", xml+"lang": "lat"})
                newElementAddName.text = resolve_text(az_person)

    # Aus Sicht des Registers:
    # gehe alle addNames durch und gucke, ob es die in der Auszeichnung gibt.
    print("\n>>>>>> CORRECTING PERSONS (Sicht d. Registers)... <<<<<<")
    for pr_person in pr_persons:
        key = pr_person.attrib[xml+'id']
        vorkommen_in_az = az_root.xpath(f".//tei:persName[@key='{key}']", namespaces=namespaces)
        all_addName = pr_person.xpath(f"./tei:persName/tei:addName[@source='catalog']", namespaces=namespaces)
        for addName in all_addName:
            for person_in_az in vorkommen_in_az:
                if resolve_text(addName) == resolve_text(person_in_az): 
                    break
            else: # wenn es ihn nicht in Auszeichnung gibt
                # dann lösche addName-Eintrag im Register
                 print(f"{key} addName {resolve_text(addName)} nicht in d. Auszeichnung gefunden. Lösche...")
                 addName.getparent().remove(addName)
        # gucke, ob Name aus @catalog auch in addNames vorhanden ist, wenn nicht, übernehme ersten addNames
        if pr_person.xpath("./tei:persName/tei:name[@source='catalog']", namespaces=namespaces):
            name = pr_person.xpath("./tei:persName/tei:name[@source='catalog']", namespaces=namespaces)[0]
            if all_addName:
                for addName in all_addName:
                    if resolve_text(name) == resolve_text(addName):
                        break
                else: # wenn es ihn nicht in addNames gibt
                    # dann nehme ersten addName
                    print(f"{key} {resolve_text(name)} nicht in addNames gefunden, ersetze mit {resolve_text(all_addName[0])}...")
                    name.text = resolve_text(all_addName[0])

def correct_serieses():
    # Aus Sicht der Auszeichnung:
    # geht alle Serien in der Auszeichnung durch und guckt, ob es schon einen addName-Eintrag im Register gibt
    print("\n>>>>>> CORRECTING SERIESES (Sicht d. Auszeichnung)... <<<<<<")
    for az_series in az_serieses:
        key = az_series.attrib['key']
        series = wr_root.xpath(f".//tei:bibl[@xml:id='{key}']", namespaces=namespaces)[0]
        all_addName_with_id = series.xpath("./tei:addName[@source='catalog']", namespaces=namespaces)
        if resolve_text(az_series):
            for addName in all_addName_with_id:
                # Wenn gleich mit addName
                if resolve_text(az_series) == resolve_text(addName):
                    break
            else: # Wenn kein addName übereinstimmt
                # Dann lege neues addName an
                print(key + " " + resolve_text(az_series) + " nicht in addNames gefunden. Lege an...")
                if series.xpath("./tei:addName", namespaces=namespaces):
                    element_to_append_to = series.xpath("./tei:addName", namespaces=namespaces)[-1]
                else:
                    element_to_append_to = series.xpath("./tei:title", namespaces=namespaces)[0]
                new_addName = etree.Element(tei+"addName", attrib={"source": "catalog"})
                new_addName.text = resolve_text(az_series)
                series.insert(series.index(element_to_append_to)+1, new_addName)


    # Aus Sicht des Registers:
    # gehe alle addNames durch und gucke, ob es die in der Auszeichnung gibt.
    print("\n>>>>>> CORRECTING SERIESES (Sicht d. Registers)... <<<<<<")
    for wr_series in wr_serieses:
        key = wr_series.attrib[xml+'id']
        vorkommen_in_az = az_root.xpath(f".//tei:title[@key='{key}']", namespaces=namespaces)
        all_addName = wr_series.xpath(f"./tei:addName[@source='catalog']", namespaces=namespaces)
        for addName in all_addName:
            for series_in_az in vorkommen_in_az:
                if resolve_text(addName) == resolve_text(series_in_az): 
                    break
            else: # wenn es ihn nicht in Auszeichnung gibt
                # dann lösche addName-Eintrag im Register
                 print(f"{key} addName {resolve_text(addName)} nicht in d. Auszeichnung gefunden. Lösche...")
                 addName.getparent().remove(addName)
        # gucke, ob Title aus @catalog auch in addNames vorhanden ist, wenn nicht, übernehme ersten addNames
        if wr_series.xpath("./tei:title[@source='catalog']/tei:title[@type='main']", namespaces=namespaces):
            title = wr_series.xpath("./tei:title[@source='catalog']/tei:title[@type='main']", namespaces=namespaces)[0]
            if all_addName:
                for addName in all_addName:
                    if resolve_text(title) == resolve_text(addName):
                        break
                else: # wenn es ihn nicht in addNames gibt
                    # dann nehme ersten addName
                    print(f"{key} {resolve_text(title)} nicht in addNames gefunden, ersetze mit {resolve_text(all_addName[0])}...")
                    title.text = resolve_text(all_addName[0])

def correct_monographs():
    # Aus Sicht der Auszeichnung:
    # geht alle Monographien in der Auszeichnung durch und guckt, ob es schon einen addName-Eintrag im Register gibt
    print("\n>>>>>> CORRECTING MONOGRAPHS (Sicht d. Auszeichnung)... <<<<<<")
    for az_monograph in az_monographs:
        key = az_monograph.attrib['key']
        monograph = wr_root.xpath(f".//tei:bibl[@xml:id='{key}']", namespaces=namespaces)[0]
        all_addName_with_id = monograph.xpath("./tei:addName[@source='catalog']", namespaces=namespaces)
        if resolve_text(az_monograph):
            for addName in all_addName_with_id:
                # Wenn gleich mit addName
                if resolve_text(az_monograph) == resolve_text(addName):
                    break
            else: # Wenn kein addName übereinstimmt
                # Dann lege neues addName an
                print(key + " " + resolve_text(az_monograph) + " nicht in addNames gefunden. Lege an...")
                if monograph.xpath("./tei:addName", namespaces=namespaces):
                    element_to_append_to = monograph.xpath("./tei:addName", namespaces=namespaces)[-1]
                else:
                    element_to_append_to = monograph.xpath("./tei:title", namespaces=namespaces)[0]
                new_addName = etree.Element(tei+"addName", attrib={"source": "catalog"})
                new_addName.text = resolve_text(az_monograph)
                monograph.insert(monograph.index(element_to_append_to)+1, new_addName)


    # Aus Sicht des Registers:
    # gehe alle addNames durch und gucke, ob es die in der Auszeichnung gibt.
    print("\n>>>>>> CORRECTING MONOGRAPHS (Sicht d. Registers)... <<<<<<")
    for wr_monograph in wr_monographs:
        key = wr_monograph.attrib[xml+'id']
        vorkommen_in_az = az_root.xpath(f".//tei:title[@key='{key}']", namespaces=namespaces)
        all_addName = wr_monograph.xpath("./tei:addName[@source='catalog']", namespaces=namespaces)
        for addName in all_addName:
            for monograph_in_az in vorkommen_in_az:
                if resolve_text(addName) == resolve_text(monograph_in_az): 
                    break
            else: # wenn es ihn nicht in Auszeichnung gibt
                # dann lösche addName-Eintrag im Register
                 print(f"{key} addName {resolve_text(addName)} nicht in d. Auszeichnung gefunden. Lösche...")
                 addName.getparent().remove(addName)
        # gucke, ob Title aus @catalog auch in addNames vorhanden ist, wenn nicht, übernehme ersten addNames
        if wr_monograph.xpath("./tei:title[@source='catalog']/tei:title[@type='main']", namespaces=namespaces):
            title = wr_monograph.xpath("./tei:title[@source='catalog']/tei:title[@type='main']", namespaces=namespaces)[0]
            if all_addName:
                for addName in all_addName:
                    if resolve_text(title) == resolve_text(addName):
                        break
                else: # wenn es ihn nicht in addNames gibt
                    # dann nehme ersten addName
                    print(f"{key} {resolve_text(title)} nicht in addNames gefunden, ersetze mit {resolve_text(all_addName[0])}...")
                    title.text = resolve_text(all_addName[0])

def correct_organisations():
    # Aus Sicht der Auszeichnung:
    # geht alle Organisationen in der Auszeichnung durch und guckt, ob es schon einen addName-Eintrag im Register gibt
    print("\n>>>>>> CORRECTING ORGANISATIONS (Sicht d. Auszeichnung)... <<<<<<")
    for az_organisation in az_organisations:
        key = az_organisation.attrib['key']
        organisation = org_root.xpath(f".//tei:org[@xml:id='{key}']", namespaces=namespaces)[0]
        all_addName_with_id = organisation.xpath("./tei:orgName/tei:addName[@source='catalog']", namespaces=namespaces)
        if resolve_text(az_organisation):
            for addName in all_addName_with_id:
                # Wenn gleich mit addName
                if resolve_text(az_organisation) == resolve_text(addName):
                    break
            else: # Wenn kein addName übereinstimmt
                # Dann lege neues addName an
                print(key + " " + resolve_text(az_organisation) + " nicht in addNames gefunden. Lege an...")
                newElementAddName = etree.SubElement(organisation.xpath("./tei:orgName", namespaces=namespaces)[0], tei+"addName", attrib={"source": "catalog", xml+"lang": "lat"})
                newElementAddName.text = resolve_text(az_organisation)
        
    # Aus Sicht des Registers:
    # gehe alle addNames durch und gucke, ob es die in der Auszeichnung gibt.
    print("\n>>>>>> CORRECTING ORGANISATIONS (Sicht d. Registers)... <<<<<<")
    for org_organisation in org_organisations:
        key = org_organisation.attrib[xml+'id']
        vorkommen_in_az = az_root.xpath(f".//tei:orgName[@key='{key}']", namespaces=namespaces)
        all_addName = org_organisation.xpath("./tei:orgName/tei:addName[@source='catalog']", namespaces=namespaces)
        for addName in all_addName:
            for organisation_in_az in vorkommen_in_az:
                if resolve_text(addName) == resolve_text(organisation_in_az): 
                    break
            else: # wenn es ihn nicht in Auszeichnung gibt
                # dann lösche addName-Eintrag im Register
                 print(f"{key} addName {resolve_text(addName)} nicht in d. Auszeichnung gefunden. Lösche...")
                 addName.getparent().remove(addName)
        # gucke, ob Name aus @catalog auch in addNames vorhanden ist, wenn nicht, übernehme ersten addNames
        if org_organisation.xpath("./tei:orgName/tei:name[@source='catalog']", namespaces=namespaces):
            name = org_organisation.xpath("./tei:orgName/tei:name[@source='catalog']", namespaces=namespaces)[0]
            if all_addName:
                for addName in all_addName:
                    if resolve_text(name) == resolve_text(addName):
                        break
                else: # wenn es ihn nicht in addNames gibt
                    # dann nehme ersten addName
                    print(f"{key} {resolve_text(name)} nicht in addNames gefunden, ersetze mit {resolve_text(all_addName[0])}...")
                    name.text = resolve_text(all_addName[0])

def correct_entities():
    correct_places()       
    correct_persons() 
    correct_serieses()
    correct_monographs()
    correct_organisations()
        
def check_for_unconnected_ids():
    pass
    # Hier von beiden Richtungen checken, ob es IDs gibt, die nicht im Register sind oder anders rum. Oder brauch ich das überhaupt? Schlägt er nicht sowieso vorher an?
print("██████████████████████████████████████████████████████████████████████████████████")     
#register_entities()
correct_entities()


az_tree.write("XML/Auszeichnung/kapuziner_pb.xml", encoding="utf-8", pretty_print=True)
or_tree.write("XML/Register/register_orte.xml", encoding="utf-8", pretty_print=True)
org_tree.write("XML/Register/register_organisationen.xml", encoding="utf-8", pretty_print=True)
pr_tree.write("XML/Register/register_personen.xml", encoding="utf-8", pretty_print=True)
wr_tree.write("XML/Register/register_werke.xml", encoding="utf-8", pretty_print=True)

currentDateAndTime = str(datetime.now())
old_log = open("Scripts/RegisterErsteller/log.txt", "r", encoding="utf-8").read()
log_text = f">>>>>> {currentDateAndTime} <<<<<<\n\n" + "\n\n".join(log) + "\n\n#########################################################################\n#########################################################################\n\n" + old_log
open("Scripts/RegisterErsteller/log.txt", "w", encoding="utf-8").write(log_text)
print("DONE!")
if log:
    print(f"\n▒▒▒▒▒▒▒▒▒▒▒ {len(log)} WARNINGS IN LOG ▒▒▒▒▒▒▒▒▒▒▒")
else:
    print("\n▒▒▒▒▒▒▒▒▒▒▒ LOG CLEAN ▒▒▒▒▒▒▒▒▒▒▒")


