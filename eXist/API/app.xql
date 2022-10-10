xquery version "3.1";

module namespace api = "http://API/templates";

declare namespace tei = "http://www.tei-c.org/ns/1.0";

import module namespace console = "http://exist-db.org/xquery/console";
import module namespace functx="http://www.functx.com";

declare variable $api:kapuziner_pb := doc("/db/apps/data/XML/Auszeichnung/kapuziner_pb.xml");
declare variable $api:register_werke := doc("/db/apps/data/XML/Register/register_werke.xml");
declare variable $api:register_personen := doc("/db/apps/data/XML/Register/register_personen.xml");
declare variable $api:register_orte := doc("/db/apps/data/XML/Register/register_orte.xml");
declare variable $api:register_organisationen := doc("/db/apps/data/XML/Register/register_organisationen.xml");
declare variable $api:lookUp := doc("/db/apps/data/XML/LookUpListen/lookUp.xml");



(:##################:)
(:### ALLGEMEIN ####:)
(:##################:)

declare function api:do-query($query) {
    let $results := switch ($query)
        case "alleAuflagen"           
            return for $result in api:get-all-editions()  
                order by $result/data(@xml:id)
                return $result
        case "allePersonen"
            return for $result in api:get-all-persons()
                order by $result/data(@xml:id)
                return $result
        case "alleOrte"
            return for $result in api:get-all-places()
                order by $result/data(@xml:id)
                return $result
        case "simpleSearch"
            return 
                api:do-simple-search()
        default return
            ()
return
    api:apply-sorting(api:apply-filters($results))
};


(: Gibt regex-Element mit Mapping zurück. :)
(:declare function api:regex-mapping($queryString) {
        <regex occur="should" boost="3">{
        functx:replace-multi($queryString, 
            ('"', '[ck]', '(æ|ä|ae?)', '(œ|ö|oe?)', '(ü|ue?)', 'ß', 'th?', '((ph)|f)', '[yij]e?'), 
            ('', '(c|k)', 'ae?', 'oe?', 'ue?', 'ss', 'th?', '((ph)|f)', '[yij]e?') 
        )
    }</regex>
};:)

declare function api:regex-mapping($queryString) {
        functx:replace-multi($queryString, 
            ('"', '[ck]', '(æ|ä|ae?)', '(œ|ö|oe?)', '(ü|ue?)', 'ß', 'th?', '((ph)|f)', '[yij]e?'), 
            ('', '(c|k)', 'ae?', 'oe?', 'ue?', 'ss', 'th?', '((ph)|f)', '[yij]e?') 
        )
};


declare function api:do-simple-search(){
    let $querySequence := api:tokenize-query-helper(request:get-parameter("simpleSearchString", ""))
    for $hit in $api:register_werke//tei:bibl[ft:query(tei:title, api:build-query($querySequence)) or ft:query(tei:addName, api:build-query($querySequence))]//tei:edition | $api:register_personen//tei:person[ft:query(tei:persName, api:build-query($querySequence))] | $api:register_orte//tei:place[ft:query(tei:placeName, api:build-query($querySequence))]
    let $score as xs:float := ft:score($hit)
    order by $score descending
    return if ($score gt 0.08) then ($hit) else ()
};

declare function api:tokenize-query-helper($input) { (: Entfernt das führende "!", ersetzt "_" durch Leerzeichen, macht es lower Case :)
    lower-case(replace(tokenize($input, "!")[last()], "_", " "))
};


declare function api:build-query($queryString) {
 (: Query fragt nach: 1. Direkter Treffer 2. Regex 3. Regex mit Wildcards 4. Fuzzy:)
    <query>
    <bool>
        {if (request:get-parameter("query", "") = "simpleSearch") then (
            <bool boost="3">{for $word in tokenize($queryString) return <term>{$word}</term>}</bool>,
            <bool boost="2">{for $word in tokenize($queryString) return <regex occur="should">{api:regex-mapping($word)}</regex>}</bool>,
            <bool boost="100">{for $word in tokenize($queryString) return <regex occur="should">.*{api:regex-mapping($word)}.*</regex>}</bool>,
            <bool>{for $word in tokenize($queryString) return <fuzzy>{$word}</fuzzy>}</bool>)
        else (
            <bool boost="3"><term>{$queryString}</term></bool>,
            <bool boost="2"><regex occur="should">{api:regex-mapping($queryString)}</regex></bool>,
            <bool boost="100"><regex occur="should">.*{api:regex-mapping($queryString)}.*</regex></bool>)}
        
    </bool>
    </query>
};

declare function api:apply-filters($results) { (: Geht alle Paramter durch und wendet die entsprechenden Filter auf die Input-Menge an :)
    let $parameters := request:get-parameter-names()
    let $edition_filterTitle_query := if ($parameters = "edition_filterTitle") then ($api:register_werke//tei:bibl[ft:query(tei:title, api:build-query(api:tokenize-query-helper(request:get-parameter("edition_filterTitle", "none")))) or ft:query(tei:addName, api:build-query(api:tokenize-query-helper(request:get-parameter("edition_filterTitle", "none"))))]//tei:edition) else ()
    let $edition_filterAuthorName_query := if ($parameters = "edition_filterAuthorName") then ($api:register_personen//tei:person[ft:query(tei:persName, api:build-query(api:tokenize-query-helper(request:get-parameter("edition_filterAuthorName", "none"))))]) else ()
    let $edition_filterPubPlaceName_query := if ($parameters = "edition_filterPubPlaceName") then ($api:register_orte//tei:place[ft:query(tei:placeName, api:build-query(api:tokenize-query-helper(request:get-parameter("edition_filterPubPlaceName", "none"))))]) else ()
    
    let $person_filterName_query := if ($parameters = "person_filterName") then ($api:register_personen//tei:person[ft:query(tei:persName, api:build-query(api:tokenize-query-helper(request:get-parameter("person_filterName", "none"))))]) else ()
    let $person_filterBirthCountryName_query := if ($parameters = "person_filterBirthCountryName") then ($api:register_orte//tei:place[ft:query(tei:country, api:build-query(api:tokenize-query-helper(request:get-parameter("person_filterBirthCountryName", "none"))))]) else ()
    let $person_filterDeathCountryName_query := if ($parameters = "person_filterDeathCountryName") then ($api:register_orte//tei:place[ft:query(tei:country, api:build-query(api:tokenize-query-helper(request:get-parameter("person_filterDeathCountryName", "none"))))]) else ()
    let $person_filterOrganisationName_query := if ($parameters = "person_filterOrganisationName") then ($api:register_organisationen//tei:org[ft:query(tei:orgName, api:build-query(api:tokenize-query-helper(request:get-parameter("person_filterOrganisationName", "none"))))]) else ()
    
    let $place_filterName_query := if ($parameters = "place_filterName") then ($api:register_orte//tei:place[ft:query(tei:placeName, api:build-query(api:tokenize-query-helper(request:get-parameter("place_filterName", "none"))))]) else ()
    let $place_filterCountryName_query := if ($parameters = "place_filterCountryName") then ($api:register_orte//tei:place[ft:query(tei:country, api:build-query(api:tokenize-query-helper(request:get-parameter("place_filterCountryName", "none"))))]) else ()


    
    
    for $hit in $results
        (: AUFLAGEN :)
        (: Druckort ID :)
        where if ($parameters = "edition_filterPubPlaceId") then
            ($hit[tei:placeName[@key = request:get-parameter("edition_filterPubPlaceId", "none")]])
        else
            ($hit)
        (: Autor ID :)
        where if ($parameters = "edition_filterAuthorId") then
            ($hit[../tei:author[@key = request:get-parameter("edition_filterAuthorId", "none")]])
        else
            ($hit)
        (: Titel :)
        where if ($parameters = "edition_filterTitle") then
            if (starts-with(request:get-parameter("edition_filterTitle", "none"), "!"))
            then ($hit[not(@xml:id=$edition_filterTitle_query/@xml:id)])
            else ($hit[@xml:id=$edition_filterTitle_query/@xml:id])
        else
            ($hit) 
        (: Autorname :)
        where if ($parameters = "edition_filterAuthorName") then
            if (starts-with(request:get-parameter("edition_filterAuthorName", "none"), "!"))
            then ($hit[not(../tei:author[@key=$edition_filterAuthorName_query/@xml:id])])
            else ($hit[../tei:author[@key=$edition_filterAuthorName_query/@xml:id]])
        else
            ($hit)
        (: Druckort :)
        where if ($parameters = "edition_filterPubPlaceName") then
            if (starts-with(request:get-parameter("edition_filterPubPlaceName", "none"), "!"))
            then ($hit[not(tei:placeName[@key=$edition_filterPubPlaceName_query/@xml:id])])
            else ($hit[tei:placeName[@key=$edition_filterPubPlaceName_query/@xml:id]])
        else
            ($hit)
        (: Erscheinungsjahr :)
        where if ($parameters = "edition_filterPubRangeOfDate") then
            (
            let $filter := request:get-parameter("edition_filterPubRangeOfDate", "none")
            let $dates := tokenize($filter, "to")
            let $minDate := if (starts-with($filter, "to")) then (xs:float("-INF")) else (xs:integer($dates[1]))
            let $maxDate := if (ends-with($filter, "to")) then (xs:float("INF")) else (if (count($dates)=1) then (xs:integer($dates[1])) else (xs:integer($dates[2])))
            return
                $hit[tei:date[xs:integer(@when-iso) >= $minDate and xs:integer(@when-iso) <= $maxDate]])
        else
            ($hit)
        (: Format :)
        where if ($parameters = "edition_filterFormat") then
          (
          let $formats := tokenize(request:get-parameter("edition_filterFormat", "none"), ",")
          return
          $hit[.//tei:dim[@n=$formats]]
          )
        else
            ($hit)
        (: Sprache :)
        where if ($parameters = "edition_filterLanguage") then
             let $lang := request:get-parameter("edition_filterLanguage", "none")
             return
            ($hit[../tei:textLang[@mainLang=$lang or tokenize(data(@otherLangs))=$lang]])
        else
            ($hit)
        (: Im Katalog :)
        where if (request:get-parameter("edition_FilterOccurence", "none") = "true") then
            ($hit[@xml:id=$api:kapuziner_pb//tei:rs[@type="edition"]/@key])
        else
            ($hit)
            
        (: PERSONEN :)
        (: Ort ID :)
        where if ($parameters = "person_filterPlaceId") then
            ($hit[tei:birth/tei:placeName[@key = request:get-parameter("person_filterPlaceId", "none")] or tei:death/tei:placeName[@key = request:get-parameter("person_filterPlaceId", "none")]])
        else
            ($hit)
        (: Name :)
        where if ($parameters = "person_filterName") then
            if (starts-with(request:get-parameter("person_filterName", "none"), "!"))
            then ($hit[not(@xml:id=$person_filterName_query/@xml:id)])
            else ($hit[@xml:id=$person_filterName_query/@xml:id])
        else
            ($hit)
        (: Geburtsland :)
        where if ($parameters = "person_filterBirthCountryName") then
            if (starts-with(request:get-parameter("person_filterBirthCountryName", "none"), "!"))
            then ($hit[not(tei:birth/tei:placeName/@key=$person_filterBirthCountryName_query/@xml:id)])
            else ($hit[tei:birth/tei:placeName/@key=$person_filterBirthCountryName_query/@xml:id])
        else
            ($hit)
        (: Todesland :)
        where if ($parameters = "person_filterDeathCountryName") then
            if (starts-with(request:get-parameter("person_filterDeathCountryName", "none"), "!"))
            then ($hit[not(tei:death/tei:placeName/@key=$person_filterDeathCountryName_query/@xml:id)])
            else ($hit[tei:death/tei:placeName/@key=$person_filterDeathCountryName_query/@xml:id])
        else
            ($hit)
        (: Organisation :)
        where if ($parameters = "person_filterOrganisationName") then
            if (starts-with(request:get-parameter("person_filterOrganisationName", "none"), "!"))
            then ($hit[not(tei:affiliation/tei:orgName/@key=$person_filterOrganisationName_query/@xml:id)])
            else ($hit[tei:affiliation/tei:orgName/@key=$person_filterOrganisationName_query/@xml:id])
        else
            ($hit)
        (: Lebenszeit :)
        where if ($parameters = "person_filterLifetimeRangeOfDate") then
            (
            let $filter := request:get-parameter("person_filterLifetimeRangeOfDate", "none")
            let $dates := tokenize($filter, "to")
            let $minDate := if (starts-with($filter, "to")) then (xs:float("-INF")) else (xs:integer($dates[1]))
            let $maxDate := if (ends-with($filter, "to")) then (xs:float("INF")) else (if (count($dates)=1) then (xs:integer($dates[1])) else (xs:integer($dates[2])))
            return
                $hit[(map:get(api:get-birth-date-range($hit), "min_date") >= $minDate and map:get(api:get-birth-date-range($hit), "min_date") <= $maxDate) or (map:get(api:get-death-date-range($hit), "max_date") >= $minDate and map:get(api:get-death-date-range($hit), "max_date") <= $maxDate)])
        else
            ($hit)
        (: Im Katalog :)
        where if (request:get-parameter("person_FilterOccurence", "none") = "true") then
            ($hit[@xml:id=$api:kapuziner_pb//tei:persName/@key])
        else
            ($hit)
        
        (: ORTE :)
        (: Name :)
        where if ($parameters = "place_filterName") then
            if (starts-with(request:get-parameter("place_filterName", "none"), "!"))
            then ($hit[not(@xml:id=$place_filterName_query/@xml:id)])
            else ($hit[@xml:id=$place_filterName_query/@xml:id])
        else
            ($hit)
        (: Land :)
        where if ($parameters = "place_filterCountryName") then
            if (starts-with(request:get-parameter("place_filterCountryName", "none"), "!"))
            then ($hit[not(@xml:id=$place_filterCountryName_query/@xml:id)])
            else ($hit[@xml:id=$place_filterCountryName_query/@xml:id])
        else
            ($hit)
        (: Im Katalog :)
        where if (request:get-parameter("place_FilterOccurence", "none") = "true") then
            ($hit[@xml:id=$api:kapuziner_pb//tei:placeName/@key])
        else
            ($hit)
            
    return
        $hit
};

declare function api:apply-sorting($results) {
    let $sortingKey := request:get-parameter("sortingKey", "none")
    let $sortingDirection := request:get-parameter("sortingDirection", "ascending")
    return switch ($sortingKey)
        case "relevance"
            return for $result in $results let $score as xs:float := ft:score($result) order by $score descending return $result
        (: AUFLAGEN :)
        case "title"
            return if ($sortingDirection = "descending") then (for $result in $results order by api:prepare-for-sorting($result/..//tei:title[@type='main']/text()) descending empty least return $result) else (for $result in $results order by api:prepare-for-sorting($result/..//tei:title[@type='main']/text()) return $result)
        case "pubDate"
            return if ($sortingDirection = "descending") then (for $result in $results order by api:get-date($result) descending empty least return $result) else (for $result in $results order by api:get-date($result) return $result)    
        (: PERSONEN :)
        case "personName"
            return if ($sortingDirection = "descending") then (for $result in $results order by api:prepare-for-sorting(api:get-person-name($result)) descending empty least return $result) else (for $result in $results order by api:prepare-for-sorting(api:get-person-name($result)) return $result)
        case "birthDate"
            return if ($sortingDirection = "descending") then (for $result in $results order by map:get(api:get-birth-date-range($result), "min_date") descending empty least return $result) else (for $result in $results order by map:get(api:get-birth-date-range($result), "min_date") return $result)
        case "deathDate"
            return if ($sortingDirection = "descending") then (for $result in $results order by map:get(api:get-death-date-range($result), "min_date") descending empty least return $result) else (for $result in $results order by map:get(api:get-death-date-range($result), "min_date") return $result)
        (: ORTE :)
        case "placeName"
            return if ($sortingDirection = "descending") then (for $result in $results order by api:prepare-for-sorting(api:get-place-name($result)) descending empty least return $result) else (for $result in $results order by api:prepare-for-sorting(api:get-place-name($result)) return $result)    
    default return ($results)      
};

declare function api:prepare-for-sorting($elem){ (: Brauche ich, weil die Funktionen normalize-space und lower-case sonst die SOrtierung mit leeren Ergebnissen zerstören und diese nicht mehr als leere Ergebnisse erkannt werden :)
    if ($elem) then (normalize-space(lower-case($elem))) else ()
};


declare function api:get-occurences-in-catalog($id) {
    let $occurencesInCatalog := 
        if (api:type-of-id($id) = "person") then
            ($api:kapuziner_pb//tei:text//tei:persName[@key = $id])
        else
            if (api:type-of-id($id) = "place") then
                ($api:kapuziner_pb//tei:text//tei:placeName[@key = $id])
            else
                if (api:type-of-id($id) = "edition") then
                    ($api:kapuziner_pb//tei:text//tei:rs[@key = $id])
                else 
                    if (api:type-of-id($id) = "series") then
                        ($api:kapuziner_pb//tei:text//tei:title[@key = $id])
                    else()
                
    let $pages := for $occurence in $occurencesInCatalog
    return
        $occurence/ancestor::tei:table/preceding-sibling::tei:pb[1]/data(@n)
    return
        distinct-values($pages)
};

declare function api:select-whole-category($category){
    $api:kapuziner_pb//tei:head[text()=$category]/ancestor::tei:table//*
};


declare function api:get-idnos($node){ (: node --> idnos :)
    $node/tei:idno
};


declare function api:get-wikidata-id($node){ (: node -> wikidata ID :)
    $node/tei:idno[@type='wikidata']/text()
};

(:##################:)
(:###### MASS ######:)
(:##################:)

declare function api:get-all-editions-ids() { (: --> Sequence of all e_ids in the catalog :)
    distinct-values($api:kapuziner_pb//tei:body//tei:rs[@type = 'edition']/@key)
};

declare function api:get-all-editions() { (: --> Sequence of all Editions in the database :)
    $api:register_werke//tei:listBibl//tei:edition
};

declare function api:get-all-persons-ids() { (: --> Sequence of all pe_ids in the catalog :)
    distinct-values($api:kapuziner_pb//tei:body//tei:persName/@key)
};

declare function api:get-all-persons() { (: --> Sequence of all Persons in the database :)
     $api:register_personen//tei:listPerson/tei:person
};

declare function api:get-all-places-ids() { (: --> Sequence of all pl_ids in the catalog :)
    distinct-values($api:kapuziner_pb//tei:body//tei:placeName/@key)
};

declare function api:get-all-places() { (: --> Sequence of all Places in the database :)
    $api:register_orte//tei:listPlace/tei:place
};

declare function api:get-all-organisations() { (: --> Sequence of all Organisations in the database :)
    $api:register_organisationen//tei:listOrg/tei:org
};



(:##################:)
(:##### SERIES #####:)
(:##################:)

declare function api:get-series-from-id($s_id) { (: s_id --> series :)
    $api:register_werke//tei:listBibl/tei:bibl[@xml:id = $s_id]
};

declare function api:get-series-maintitle($series) { (: series --> maintitle :)
    normalize-space($series/tei:title/tei:title[@type = "main"]/text())
};

declare function api:get-series-title-sources($series) { (: series --> sources :)
    $series/tei:title/data(@source)
};

declare function api:get-series-subtitle($series) { (: series --> subtitle :)
    normalize-space($series/tei:title/tei:title[@type = "sub"]/text())
};

declare function api:get-series-addNames-from-catalog($series){ (: series --> addNames :)
    $series/tei:addName[@source="catalog"]/text()
};

declare function api:get-monographs-from-series($series) { (: series --> monographs :)
    $series/tei:bibl[@type = "m"]
};


(:##################:)
(:### MONOGRAPH ####:)
(:##################:)

declare function api:get-monograph-maintitle($monograph) { (: monograph --> maintitle :)
    normalize-space($monograph//tei:title[@type = "main"]/text())
};

declare function api:get-monograph-title-sources($monograph) { (: monograph --> sources :)
    $monograph//tei:title/data(@source)
};

declare function api:get-monograph-subtitle($monograph) { (: monograph --> subtitle :)
    normalize-space($monograph//tei:title[@type = "sub"]/text())
};

declare function api:is-part-of-series($monograph) { (: monograph --> boolean :)
    boolean($monograph/parent::tei:bibl[@type = "s"])
};

declare function api:get-series-from-monograph($monograph) { (: monograph --> series :)
    $monograph/parent::tei:bibl[@type = "s"]
};

declare function api:is-volume($monograph) { (: monograph --> boolean :)
    boolean($monograph/tei:biblScope[@unit = "volume"])
};

declare function api:get-volume-number($monograph) { (: monograph --> volume number :)
    xs:integer($monograph/tei:biblScope[@unit = "volume"]/data(@n))
};

declare function api:get-editions-from-monograph($monograph) { (: monograph --> editions :)
    $monograph/tei:edition
};

declare function api:has-authors($monograph) { (: monograph --> boolean :)
    boolean($monograph/tei:author)
};

declare function api:get-authors-ids($monograph) { (: monograph --> author ids :)
    $monograph/tei:author/data(@key)
};

declare function api:get-authors-sources($monograph) { (: monograph --> sources :)
    $monograph/tei:author/data(@source)
};

declare function api:has-editors($monograph) { (: monograph --> boolean :)
    boolean($monograph/tei:editor)
};

declare function api:get-editors-sources($monograph) { (: monograph --> sources :)
    $monograph/tei:editor/data(@source)
};

declare function api:get-editors-ids($monograph) { (: monograph --> editor ids :)
    $monograph/tei:editor/data(@key)
};

declare function api:get-monograph-addNames-from-catalog($monograph){ (: monograph --> addNames :)
    $monograph/tei:addName[@source="catalog"]/text()
};

declare function api:get-main-language($monograph) { (: monograph --> main language :)
    $monograph/tei:textLang/data(@mainLang)
};

declare function api:get-all-languages($monograph) { (: monograph --> all languages :)
    let $main_language := if ($monograph/tei:textLang/data(@mainLang) eq "mul") then () else ($monograph/tei:textLang/data(@mainLang))
    let $other_languages := for $lang in tokenize($monograph/tei:textLang/data(@otherLangs)) return $lang
    return ($main_language, $other_languages)
};

declare function api:get-all-languages-sources($monograph) { (: monograph --> sources :)
    let $main_language := if ($monograph/tei:textLang/data(@mainLang) eq "mul") then () else ($monograph/tei:textLang/data(@source))
    let $other_languages := for $lang in tokenize($monograph/tei:textLang/data(@otherLangs)) return $monograph/tei:textLang/data(@source)
    return ($main_language, $other_languages)
};


(:##################:)
(:#### EDITION #####:)
(:##################:)

declare function api:get-edition-from-id($e_id) { (: e_id --> edition :)
    $api:register_werke//tei:bibl/tei:edition[@xml:id = $e_id]
};

declare function api:get-monograph-from-edition($edition) { (: edition --> monograph :)
    $edition/parent::tei:bibl[@type = "m"]
};

declare function api:has-places($edition) { (: edition --> boolean :)
    boolean($edition/tei:placeName)
};

declare function api:get-places-ids($edition) { (: edition --> sequence of pl_ids :)
    $edition/tei:placeName/data(@key)
};

declare function api:get-places-sources($edition) { (: edition --> sources :)
    $edition/tei:placeName/data(@source)
};

declare function api:get-places($edition) { (: edition --> places :)
    $api:register_orte//tei:listPlace/tei:place[@xml:id = api:get-places-ids($edition)]
};

declare function api:has-date($edition) { (: edition --> boolean :)
    boolean($edition/tei:date)
};

declare function api:get-date($edition) { (: edition --> date :)
    xs:integer($edition/tei:date/data(@when-iso))
};

declare function api:get-date-sources($edition) { (: edition --> sources :)
    $edition/tei:date/data(@source)
};

declare function api:has-dimensions($edition) { (: edition --> boolean :)
    boolean($edition/tei:dimensions)
};

declare function api:get-dimensions($edition) { (: edition --> dimensions :)
    xs:integer($edition/tei:dimensions/tei:dim[@type='folio']/data(@n))
};

declare function api:get-dimensions-sources($edition) { (: edition --> sources :)
    $edition/tei:dimensions/data(@source)
};

declare function api:get-other-editions($edition){ (: edition --> editions :)
    $edition/preceding-sibling::tei:edition | $edition/following-sibling::tei:edition
};

declare function api:get-first-occurence-in-catalog($edition){
    $api:kapuziner_pb//tei:text//tei:rs[@type='edition' and @key=$edition/@xml:id][1]
};


declare function api:get-category-from-pageNumber($pageNumber){ (: PageNumber -> Kategorie im Katalog :) 
    let $categories := map {"Sacra Scriptura": (9,18),
                            "Sancti Patres": (19,24), 
                            "Scriptores Ecclesiastici": (25,28),
                            "Scriptores Ordinum Religiosorum": (29,36),
                            "Expositores Sacræ Scripturæ": (37,48),
                            "Libri Ascetici": (49,80),
                            "Canonistæ": (81,94),
                            "Concilia &amp; Canones": (95,100),
                            "Theologi": (101,132),
                            "Controversistæ": (133,158),
                            "Philosophi": (159,168),
                            "Juristæ": (169,180),
                            "Concionatores": (181,240),
                            "Catechistæ": (241,243),
                            "Libri Infirmorum": (244,245),
                            "Libri Exorcismorum": (246,246),
                            "Historici Sacri": (247,254),
                            "Historici Profani": (255,266),
                            "Miscellanei": (267,278),
                            "Rhetores": (279,284),
                            "Pöetæ": (285,290),
                            "Libri Gallici": (291,298),
                            "Libri Italici, Hispanici &amp; Belgici &amp;c.": (299,310)
                            }

   for $category in map:keys($categories)
   where ($pageNumber ge map:get($categories, $category)[1] and $pageNumber le map:get($categories, $category)[2])
   return $category

    
};

declare function api:get-pageNumber-of-entity($entity){ (: entity in catalog -> Seitenzahl im Katalog (Scanseiten) :)
    xs:integer($entity/ancestor::tei:table/preceding-sibling::tei:pb[1]/data(@n))
};


(: Falls ichs brauche, muss ich es umschreiben, funktioniert noch mit den alten Kategoiren, die nicht zwischen drei O's unterscheiden :)
(:declare function api:get-position-in-category($edition){ (\: edition -> Position im Katalog :\)
    let $sequence := api:select-whole-category(api:get-category($edition))//tei:rs[@type='edition']/@key
    return index-of($sequence, $edition/@xml:id)
};:)


(:##################:)
(:##### PERSON #####:)
(:##################:)

declare function api:get-person-name($person) { (: person --> name :)
    $person/tei:persName/tei:name/text()
};

declare function api:get-person-name-sources($person) { (: person --> sources :)
    $person/tei:persName/tei:name/data(@source)
};

declare function api:get-person-by-id($pe_id) { (: pe_id --> person :)
    $api:register_personen//tei:person[@xml:id = $pe_id]
};

declare function api:get-person-addNames-from-catalog($person){ (: person --> addNames :)
    $person/tei:persName/tei:addName[@source="catalog"]/text()
};

declare function api:get-person-sex($person) { (: person --> sex :)
    $person/tei:sex/data(@value)
};

declare function api:get-person-sex-sources($person) { (: person --> sources :)
    $person/tei:sex/data(@source)
};

declare function api:has-birth($person){ (: person --> boolean :)
    boolean($person/tei:birth)
};

declare function api:has-birth-place($person){ (: person --> boolean :)
    boolean($person/tei:birth/tei:placeName/@key)
};

declare function api:get-birth-place($person) { (: person --> place :)
    if (api:has-birth-place($person)) then ($api:register_orte//tei:listPlace/tei:place[@xml:id = $person/tei:birth/tei:placeName/data(@key)]) else ()
};

declare function api:get-birth-place-sources($person){ (: person --> sources :)
    $person/tei:birth/tei:placeName/data(@source)
};

declare function api:has-death($person){ (: person --> boolean :)
    boolean($person/tei:death)
};

declare function api:has-death-place($person){ (: person --> boolean :)
    boolean($person/tei:death/tei:placeName/@key)
};

declare function api:get-death-place($person) { (: person --> place :)
    if (api:has-death-place($person)) then ($api:register_orte//tei:listPlace/tei:place[@xml:id = $person/tei:death/tei:placeName/data(@key)]) else ()
};

declare function api:get-death-place-sources($person){ (: person --> sources :)
    $person/tei:death/tei:placeName/data(@source)
};

declare function api:has-birth-date($person) { (: person --> boolean :)
    boolean($person/tei:birth/tei:date)
};

declare function api:get-birth-date-range($person) { (: person --> map of min and max date :)
    let $min_date := if ($person/tei:birth/tei:date/@when-iso) then (xs:integer($person/tei:birth/tei:date/data(@when-iso))) else (xs:integer($person/tei:birth/tei:date/data(@notBefore-iso)))
    let $max_date := if ($person/tei:birth/tei:date/@when-iso) then (xs:integer($person/tei:birth/tei:date/data(@when-iso))) else (xs:integer($person/tei:birth/tei:date/data(@notAfter-iso)))
    return map {"min_date": $min_date, "max_date": $max_date}
};

declare function api:get-birth-date-sources($person) { (: person --> sources :)
    $person/tei:birth/tei:date/data(@source)
};

declare function api:has-death-date($person) { (: person --> boolean :)
    boolean($person/tei:death/tei:date)
};

declare function api:get-death-date-range($person) { (: person --> map of min and max date :)
    let $min_date := if ($person/tei:death/tei:date/@when-iso) then (xs:integer($person/tei:death/tei:date/data(@when-iso))) else (xs:integer($person/tei:death/tei:date/data(@notBefore-iso)))
    let $max_date := if ($person/tei:death/tei:date/@when-iso) then (xs:integer($person/tei:death/tei:date/data(@when-iso))) else (xs:integer($person/tei:death/tei:date/data(@notAfter-iso)))
    return map {"min_date": $min_date, "max_date": $max_date}
};

declare function api:get-death-date-sources($person) { (: person --> sources :)
    $person/tei:death/tei:date/data(@source)
};

declare function api:has-organisations($person){
    boolean($person/tei:affiliation/tei:orgName/@key)
};

declare function api:get-organisations($person) { (: person --> organisations :)
    $api:register_organisationen//tei:listOrg/tei:org[@xml:id = $person/tei:affiliation/tei:orgName/data(@key)]
};

declare function api:get-organisations-sources($person){
    $person/tei:affiliation/tei:orgName/data(@source)
};



(:##################:)
(:###### PLACE #####:)
(:##################:)

declare function api:get-place-by-id($pl_id) { (: pl_id --> place :)
    $api:register_orte//tei:place[@xml:id = $pl_id]
};

declare function api:get-place-name($place) { (: place --> name :)
    $place/tei:placeName/tei:name/text()
};

declare function api:get-place-name-sources($place) { (: place --> sources :)
    $place/tei:placeName/tei:name/data(@source)
};

declare function api:get-place-addNames-from-catalog($place){ (: place --> addNames :)
    $place/tei:placeName/tei:addName[@source="catalog"]/text()
};

declare function api:get-country($place) { (: place --> country :)
    $place/tei:country/text()
};

declare function api:get-country-sources($place) { (: place --> sources :)
    $place/tei:country/data(@source)
};

declare function api:get-coordinates($place) { (: place --> coordinates :)
    $place/tei:location/tei:geo/text()
};

declare function api:get-coordinates-sources($place) { (: place --> sources :)
    $place/tei:location/tei:geo/data(@source)
};


(:##################:)
(:## ORGANISATION ##:)
(:##################:)

declare function api:get-organisation-by-id($org_id) { (: org_id --> organisation :)
    $api:register_organisationen//tei:org[@xml:id = $org_id]
};

declare function api:get-organisation-name($organisation) { (: organisation --> name :)
    $organisation/tei:orgName/tei:name/text()
};

declare function api:get-organisation-addNames-from-catalog($organisation){ (: organisation --> addNames :)
    $organisation/tei:orgName/tei:addName[@source="catalog"]/text()
};




(:##################:)
(:##### HELPER #####:)
(:##################:)

declare function api:type-of-id($id) { (: id --> type of id, z.B. "series" :)
    if (matches($id, "^m_[0-9]{5}_[a-z]$")) then
        ("edition")
    else
        if (matches($id, "^m_[0-9]{5}$")) then
            ("monograph")
        else
            if (matches($id, "^s_[0-9]{5}$")) then
                ("series")
            else
                if (matches($id, "^pl_[0-9]{5}$")) then
                    ("place")
                else
                    if (matches($id, "^pe_[0-9]{5}$")) then
                        ("person")
                    else
                        ()
};

declare function api:type-of-node($node) { (: node --> type of node, z.B. "series" :)
    if ($node/name() = "edition") then
        ("edition")
    else
        if ($node/name() = "bibl" and $node[@type = "m"]) then
            ("monograph")
        else
            if ($node/name() = "bibl" and $node[@type = "s"]) then
                ("series")
            else
                if ($node/name() = "place") then
                    ("place")
                else
                    if ($node/name() = "person") then
                        ("person")
                    else
                        ()
};

declare function api:look-up-list($type, $abbr){ (: type of abbreviation, abbreviation --> expansion :)
    $api:lookUp//tei:list[@type=$type]//tei:abbr[text()=$abbr]/following-sibling::tei:expan[1]/text()
};












