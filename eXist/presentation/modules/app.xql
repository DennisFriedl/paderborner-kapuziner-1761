xquery version "3.1";

module namespace app = "http://presentation/templates";

import module namespace api = "http://API/templates" at "/db/apps/API/app.xql";
declare namespace tei="http://www.tei-c.org/ns/1.0";
import module namespace templates = "http://exist-db.org/xquery/templates";
import module namespace config = "http://presentation/config" at "config.xqm";

import module namespace console="http://exist-db.org/xquery/console";

declare variable $app:SESSION := "datenbank:results-col";
declare variable $app:hitsPerPage := 10;


(:##################:)
(:##### EDITION ####:)
(:##################:)

declare
%templates:wrap
function app:XMLtoHTML ($node as node(), $model as map (*)) {
    let $page := xs:string(request:get-parameter("page", ""))
    let $params := <parameters>
                        <param name="page" value="{$page}"/>
                    </parameters>
    let $kapuziner_pb := doc("/db/apps/data/XML/Auszeichnung/kapuziner_pb.xml")
    let $xsl := doc("/db/apps/presentation/resources/xslt/XMLtoHTML.xsl")
    return transform:transform($kapuziner_pb, $xsl, $params)
};



(:##################:)
(:###### QUERY #####:)
(:##################:)


declare
%templates:wrap
%templates:default("query", "false")
%templates:default("resetCache", "false")
function app:query($node as node()*, $model as map(*), $query as xs:string, $resetCache as xs:string) {
response:set-header("Cache-Control", "no-cache , no-store, must-revalidate"), (: Verhindert das Anlegen eines Caches im Browser, hatte da Probleme beim Umblättern :)
if ($query != "false") then
    if (session:exists() and $resetCache = "false") then map:entry("hits", session:get-attribute($app:SESSION))
    else
        (session:create(),
        let $hits := api:do-query($query)
        let $store := session:set-attribute($app:SESSION, $hits)
        return
            map:entry("hits", $hits))
else ()
};





declare
    %templates:wrap
function app:hit-count($node as node()*, $model as map(*)) {
    let $hits := count($model("hits"))
    return
    if ($hits = 1) then
    <h2>{$hits} Ergebnis</h2>
    else
    <h2>{$hits} Ergebnisse</h2>
};

declare
%templates:default("page", 1)
function app:show-hits($node as node()*, $model as map(*), $page as xs:int) {
    let $start := $page * $app:hitsPerPage - $app:hitsPerPage + 1
    for $hit in subsequence($model("hits"), $start, $app:hitsPerPage)
    return
        app:build-card($hit)
};

declare
function app:show-sortings($node as node()*, $model as map(*)) {
    <select class="form-control" id="sorting-form-control" onchange="setSortingParameters(this.value)">
    <option value="relevance-descending" selected="">Relevanz</option>
    {    
    if ($model("hits")/../tei:edition) then (<option value="title-ascending">Titel &#129145;</option>,<option value="title-descending">Titel &#129147;</option>,<option value="pubDate-ascending">Erscheinungsjahr &#129145;</option>,<option value="pubDate-descending">Erscheinungsjahr &#129147;</option>) else (),
    if ($model("hits")/../tei:person) then (<option value="personName-ascending">Personenname &#129145;</option>,<option value="personName-descending">Personenname &#129147;</option>,<option value="birthDate-ascending">Geburtsdatum &#129145;</option>,<option value="birthDate-descending">Geburtsdatum &#129147;</option>,<option value="deathDate-ascending">Todesdatum &#129145;</option>,<option value="deathDate-descending">Todesdatum &#129147;</option>) else (),
    if ($model("hits")/../tei:place) then (<option value="placeName-ascending">Ortsname &#129145;</option>,<option value="placeName-descending">Ortsname &#129147;</option>) else ()   
    }
    </select>
};

declare
    %templates:wrap
function app:create-paging-data($node as node()*, $model as map(*)) {
    let $hits := count($model("hits"))
    return 
    <nav class="paging-nav"><ul class="pagination pagination-lg justify-content-center" id="paging-ul" data-hits="{$hits}" data-hitsPerPage="{$app:hitsPerPage}"></ul></nav>
};

declare function app:build-card($hit){
    if (api:type-of-node($hit) = "edition") then app:build-edition-card($hit) 
    else if (api:type-of-node($hit) = "person") then app:build-person-card($hit)
    else if (api:type-of-node($hit) = "place") then app:build-place-card($hit)
    else()
};


(:#########################:)
(:###### AUFLAGE CARD #####:)
(:#########################:)

declare function app:build-edition-card($edition){
    let $monograph := api:get-monograph-from-edition($edition)
    return
    <div class="card">
    <div class="card-body">
    <div class="row"><div class="col col-6"><p class="result-type"><i class="fas fa-book"/> Auflage <span class="small-id">{$edition/data(@xml:id)}</span></p></div><div class="col col-6"><a class="button button-small" href="auflage.html?id={$edition/data(@xml:id)}"><i class="fas fa-angle-double-right"/> Ganzer Datensatz</a></div></div>
    <h5 class="card-title limited-lines">{app:construct-title($monograph)}</h5>
    {if (api:is-part-of-series($monograph)) then (<h6 class="card-subtitle mb-2 limited-lines series-title">{app:construct-series-title($monograph)}</h6>) else ()}
    {if (api:has-authors($monograph)) then (<p class="card-text"><i class="fas fa-user"/>{((" "),  app:list-with-commas(app:construct-persons($monograph, api:get-authors-ids($monograph))))}</p>) else ()}
    {if (api:has-places($edition) or api:has-date($edition)) then (<p class="card-text">{if (api:has-places($edition)) then (<i class="fas fa-map-marker-alt"/>,((" "), app:list-with-commas(app:construct-places($edition)), (" "))) else (), if (api:has-date($edition)) then (<i class="fas fa-clock"/>,((" "), api:get-date($edition))) else ()}</p>) else ()}
    </div>
    </div>
};

declare function app:construct-title($node){
let $mainTitle := if (api:type-of-node($node) = "monograph") then (api:get-monograph-maintitle($node)) else if (api:type-of-node($node) = "series") then (api:get-series-maintitle($node)) else()
let $subTitle := if (api:type-of-node($node) = "monograph") then (api:get-monograph-subtitle($node)) else if (api:type-of-node($node) = "series") then (api:get-series-subtitle($node)) else()
let $fullTitle :=  if (string-length($subTitle) > 0) then concat($mainTitle, ". ", $subTitle) else ($mainTitle)
return
   if (string-length($fullTitle) > 0) then $fullTitle
   else ("[Ohne Titel]")
};


declare function app:construct-series-title($monograph){
(
if (api:is-volume($monograph)) then ("Vol. ", api:get-volume-number($monograph), " von: ") else ("Teil von: ")
, <a href="serie.html?id={api:get-series-from-monograph($monograph)/data(@xml:id)}">{app:construct-title(api:get-series-from-monograph($monograph))}</a>)
};

declare function app:construct-persons($monograph, $listOfPersonIds){ 
 let $listWithLinks := for $pe_id in $listOfPersonIds return (<a href="person.html?id={$pe_id}">{api:get-person-name(api:get-person-by-id($pe_id))}</a>)
 return
   $listWithLinks
};


declare function app:construct-places($edition){
let $listOfPlaces := api:get-places($edition)
let $listWithLinks := for $place in $listOfPlaces return (<a href="ort.html?id={$place/data(@xml:id)}">{$place//tei:placeName/tei:name/text()}</a>)
return
    $listWithLinks
};



(:#########################:)
(:###### PERSON CARD ######:)
(:#########################:)

declare function app:build-person-card($person){
<div class="card">
<div class="card-body">
<div class="row"><div class="col col-6"><p class="result-type"><i class="fas fa-user"/> Person <span class="small-id">{$person/data(@xml:id)}</span></p></div><div class="col col-6"><a class="button button-small" href="person.html?id={$person/@xml:id}"><i class="fas fa-angle-double-right"/> Ganzer Datensatz</a></div></div>
<h5 class="card-title limited-lines">{api:get-person-name($person)}</h5>
{if (api:has-birth($person) or api:has-death($person)) then (<p class="card-text">{if (api:has-birth-date($person)) then (<i class="fas fa-star-of-life"/>, (" "), app:construct-date-range(api:get-birth-date-range($person)), (" ")) else (), if (api:has-death-date($person)) then (<i class="fas fa-cross"/>, (" "), app:construct-date-range(api:get-death-date-range($person))) else ()}</p>) else ()}
</div>
</div>
};

declare function app:construct-date-range($map){
    if (map:get($map, "min_date") eq map:get($map, "max_date")) then (map:get($map, "min_date")) else (concat("zw. ", map:get($map, "min_date"), " u. ", map:get($map, "max_date")))
};

(:#########################:)
(:######## ORT CARD #######:)
(:#########################:)

declare function app:build-place-card($place){
<div class="card">
<div class="card-body">
<div class="row"><div class="col col-6"><p class="result-type"><i class="fas fa-map-marker-alt"/> Ort <span class="small-id">{$place/data(@xml:id)}</span></p></div><div class="col col-6"><a class="button button-small" href="ort.html?id={$place/@xml:id}"><i class="fas fa-angle-double-right"/> Ganzer Datensatz</a></div></div>
<h5 class="card-title limited-lines">{api:get-place-name($place)}</h5>
</div>
</div>
};

(:#########################:)
(:####### SERIE PAGE ######:)
(:#########################:)

declare 
%templates:wrap
function app:show-series-page($node as node()*, $model as map(*), $id as xs:string){
    let $series := api:get-series-from-id($id)
    return 
        if ($series) then (
        <div class="container">
        <div class="row d-flex justify-content-center">
        <div class="col col-lg-10 col-xl-8">
        <h3 id="entity-class"><i class="fas fa-folder-open"/> Mehrbändiges Werk</h3>
        <p id="entity-id">{$id}</p>
        <h1>{if (api:get-series-maintitle($series)) then (app:wrap-in-toolbox(api:get-series-maintitle($series), api:get-series-title-sources($series))) else ("[Ohne Titel]")}</h1>
        <p id="subtitle">{api:get-series-subtitle($series)}</p>
        <h4>Daten:</h4>
        <ul>
        <li><span class="low-opacity">Namen im Katalog: </span>{if(api:get-series-addNames-from-catalog($series)) then (<span class="bold">{app:list-with-commas(api:get-series-addNames-from-catalog($series))}</span>) else ("[Ohne Titel]")}</li>
        </ul>
        <h4>In diesem mehrbändigen Werk:</h4>
        <ul>
        {for $monograph in api:get-monographs-from-series($series)
        order by api:get-volume-number($monograph) ascending
        return
            <li>
            {if (api:is-volume($monograph)) then concat("Vol. ", api:get-volume-number($monograph), ": ") else ()}
            {if (api:has-authors($monograph)) then (app:list-with-commas(app:construct-persons($monograph, api:get-authors-ids($monograph)))) else ("[Ohne Autor]")}:
            {if (api:get-monograph-maintitle($monograph)) then (concat(api:get-monograph-maintitle($monograph), ". ", api:get-monograph-subtitle($monograph))) else ("[Ohne Titel]")}
            <ul class="fa-ul">
            {for $edition in api:get-editions-from-monograph($monograph)
            order by api:get-date($edition) ascending
            return
                <li>
                <span class="fa-li"><i class="fas fa-book"/></span>
                <a href="auflage.html?id={$edition/data(@xml:id)}">
                {if (api:has-places($edition)) then(app:list-with-commas(api:get-place-name(api:get-places($edition)))) else ("[Ohne Ort]")}
                {concat(" ", if (api:has-date($edition)) then (api:get-date($edition)) else ('[Ohne Datum]'))}
                </a>
                </li>
            }
            </ul>
            </li>
        }
        </ul>
        <h4>Vorkommen im Katalog:</h4>
        <p>{if (app:construct-occurence-in-catalog($id)) then (<span class="low-opacity">[Auf Seiten:] </span>,app:construct-occurence-in-catalog($id)) else ("[Ohne Vorkommen]")}</p>
        </div>
        </div>
        </div>
    ) else (<h1>[Diese Entität existiert nicht]</h1>)
};

(:#########################:)
(:###### AUFLAGE PAGE #####:)
(:#########################:)

declare 
%templates:wrap
function app:show-edition-page($node as node()*, $model as map(*), $id as xs:string){
    let $edition := api:get-edition-from-id($id)
    let $monograph := api:get-monograph-from-edition($edition)
    return 
        if ($edition) then (
        <div class="container">
        <div class="row d-flex justify-content-center">
        <div class="col col-lg-10 col-xl-8">
        <h3 id="entity-class"><i class="fas fa-book"/> Auflage</h3>
        <p id="entity-id">{$id}</p>
        <h1>{if (api:get-monograph-maintitle($monograph)) then (app:wrap-in-toolbox(api:get-monograph-maintitle($monograph), api:get-monograph-title-sources($monograph))) else ("[Ohne Titel]")}</h1>
        <p id="subtitle">{api:get-monograph-subtitle($monograph)}</p>
        <h4>Daten:</h4>
        <ul>
            <li><span class="low-opacity">Namen im Katalog: </span>{if (api:get-monograph-addNames-from-catalog($monograph)) then (<span class="bold">{app:list-with-commas(api:get-monograph-addNames-from-catalog($monograph))}</span>) else ("[Ohne Titel]")}</li>
            {if (api:is-part-of-series($monograph)) then (<li><span class="bold">{app:construct-series-title($monograph)}</span></li>) else ()}
            {if (api:has-authors($monograph)) then (<li><i class="fas fa-user"/>{(<span class="low-opacity"> Autoren: </span>, <span class="bold">{app:list-with-commas(app:wrap-in-toolbox(app:construct-persons($monograph, api:get-authors-ids($monograph)), api:get-authors-sources($monograph)))}</span>)}</li>) else ()}
            {if (api:has-editors($monograph)) then (<li><i class="fas fa-user"/>{(<span class="low-opacity"> Editoren: </span>, <span class="bold">{app:list-with-commas(app:wrap-in-toolbox(app:construct-persons($monograph, api:get-editors-ids($monograph)), api:get-editors-sources($monograph)))}</span>)}</li>) else ()}
            <li><i class="fas fa-language"></i><span class="low-opacity"> Sprache: </span><span class="bold">{app:list-with-commas(app:wrap-in-toolbox(api:look-up-list('lang', api:get-all-languages($monograph)), api:get-all-languages-sources($monograph)))}</span></li>
            <li><i class="fas fa-map-marker-alt"/><span class="low-opacity"> Erscheinungsorte: </span>{if (api:has-places($edition)) then(<span class="bold"> {app:list-with-commas(app:wrap-in-toolbox(app:construct-places($edition), api:get-places-sources($edition)))} </span>) else ("[Unbekannt]")}</li>
            <li><i class="fas fa-clock"/><span class="low-opacity"> Erscheinungsjahr: </span>{if (api:has-date($edition)) then (<span class="bold"> {app:wrap-in-toolbox(api:get-date($edition), api:get-date-sources($edition))}</span>) else ('[Unbekannt]')}</li>
            <li><i class="fas fa-ruler-combined"></i><span class="low-opacity"> Format: </span>{if (api:has-dimensions($edition)) then (<span class="bold">{app:wrap-in-toolbox(app:construct-dimensions($edition), api:get-dimensions-sources($edition))}</span>) else ("[Unbekannt]")}</li>
        </ul>
        {if (api:get-idnos($edition)) then (<h4>Externe Ressourcen:</h4>,<ul>{app:construct-idnos(api:get-idnos($edition))}</ul>) else()}
        { if (api:get-other-editions($edition)) then(
        <h4>Andere Auflagen:</h4>,
        <ul class="fa-ul">
            {for $edition in api:get-other-editions($edition)
            order by api:get-date($edition) ascending
            return
                <li>
                <span class="fa-li"><i class="fas fa-book"/></span>
                <a href="auflage.html?id={$edition/data(@xml:id)}">
                {if (api:has-places($edition)) then(app:list-with-commas(api:get-place-name(api:get-places($edition)))) else ("[Ohne Ort]")}
                {concat(" ", if (api:has-date($edition)) then (api:get-date($edition)) else ('[Ohne Datum]'))}
                </a>
                </li>
            }
            </ul>
        )
        else()
        }
        <h4>Vorkommen im Katalog:</h4>
        <p>{if(app:construct-occurence-in-catalog($id)) then(<span class="low-opacity">[Auf Seiten:] </span>,app:construct-occurence-in-catalog($id)) else("[Ohne Vorkommen]")}</p>
        </div>
        </div>
        </div>
        )
        else (<h1>[Diese Entität existiert nicht]</h1>)
};

declare function app:construct-dimensions($edition){
    let $format := api:get-dimensions($edition)
    let $expan := api:look-up-list('format', $format)
    return
        concat($format, '° [', $expan, ']')
};


declare function app:construct-occurence-in-catalog($id){
    let $listOfOccurences := api:get-occurences-in-catalog($id)
    let $listWithLinks := for $occurence in $listOfOccurences return (<a href="edition.html?page={$occurence}">{$occurence}</a>)
    return
        if ($listWithLinks) then (app:list-with-commas($listWithLinks)) else()
};


(:#########################:)
(:###### PERSON PAGE ######:)
(:#########################:)

declare 
%templates:wrap
function app:show-person-page($node as node()*, $model as map(*), $id as xs:string){
    let $person := api:get-person-by-id($id)
    return
    if ($person) then (
    <div class="container">
    <div class="row d-flex justify-content-center">
    <div class="col col-lg-10 col-xl-8">
    <h3 id="entity-class"><i class="fas fa-user"/> Person</h3>
    <p id="entity-id">{$id}</p>
    <h1>{if (api:get-person-name($person)) then (app:wrap-in-toolbox(api:get-person-name($person), api:get-person-name-sources($person))) else ("[Ohne Namen]")}</h1>
    <div class="row">   
    <div class="col col-md-8 col-12 order-last order-md-first">
    <h4>Daten:</h4>
    <ul>
        <li><span class="low-opacity">Namen im Katalog: </span>{if (api:get-person-addNames-from-catalog($person)) then (<span class="bold">{app:list-with-commas(api:get-person-addNames-from-catalog($person))}</span>) else ("[Ohne Namen]")}</li>
        <li><span class="low-opacity">Geschlecht: </span>{if (api:get-person-sex($person)) then (<span class="bold">{app:wrap-in-toolbox(api:look-up-list("sex", api:get-person-sex($person)), api:get-person-sex-sources($person))}</span>) else ("[Unbekannt]")}</li>
        <li><i class="fas fa-star-of-life"></i><span class="low-opacity"> Geburt: </span>
            <ul><li><i class="fas fa-map-marker-alt"/><span class="low-opacity"> Ort: </span>{if (api:has-birth-place($person)) then (<a href="ort.html?id={api:get-birth-place($person)/data(@xml:id)}"><span class="bold">{app:wrap-in-toolbox(api:get-place-name(api:get-birth-place($person)), api:get-birth-place-sources($person))}</span></a>) else ("[Unbekannt]")}</li></ul>
            <ul><li><i class="fas fa-clock"/><span class="low-opacity"> Datum: </span>{if (api:has-birth-date($person)) then (<span class="bold">{app:wrap-in-toolbox(app:construct-date-range(api:get-birth-date-range($person)), api:get-birth-date-sources($person))}</span>) else ("[Unbekannt]")}</li></ul>
        </li>
        <li><i class="fas fa-cross"></i><span class="low-opacity"> Tod: </span>
            <ul><li><i class="fas fa-map-marker-alt"/><span class="low-opacity"> Ort: </span>{if (api:has-death-place($person)) then (<a href="ort.html?id={api:get-death-place($person)/data(@xml:id)}"><span class="bold">{app:wrap-in-toolbox(api:get-place-name(api:get-death-place($person)), api:get-death-place-sources($person))}</span></a>) else ("[Unbekannt]")}</li></ul>
            <ul><li><i class="fas fa-clock"/><span class="low-opacity"> Datum: </span>{if (api:has-death-date($person)) then (<span class="bold">{app:wrap-in-toolbox(app:construct-date-range(api:get-death-date-range($person)), api:get-death-date-sources($person))}</span>) else ("[Unbekannt]")}</li></ul>
        </li>
        {if (api:has-organisations($person)) then (<li><span class="low-opacity">Organisationen: </span><span class="bold">{app:list-with-commas(app:wrap-in-toolbox(api:get-organisation-name(api:get-organisations($person)), api:get-organisations-sources($person)))}</span></li>) else ()}       
    </ul>
    {if (api:get-idnos($person)) then (<h4>Externe Ressourcen:</h4>,<ul>{app:construct-idnos(api:get-idnos($person))}</ul>) else()}
    </div>
    <div class="col col-md-4 col-12 order-first order-md-last" id="entity-image-col">
    <figure class="figure">
    <div id="entity-image-container">
    <img id="entity-image" src="../resources/images/fa_person.png" alt="Bild" class="figure-img"/>
    </div>
    <figcaption id="entity-image-caption" class="figure-caption text-center">Suche Bild...</figcaption>
    </figure>
    </div>
    </div>  
    <h4>Vorkommen im Katalog:</h4>
    <p>{if(app:construct-occurence-in-catalog($id)) then(<span class="low-opacity">[Auf Seiten:] </span>,app:construct-occurence-in-catalog($id)) else("[Ohne Vorkommen]")}</p>
    <h4>Aktionen:</h4>
    <p><a href="datenbank.html?query=alleAuflagen&amp;edition_filterAuthorId={$id}&amp;resetCache=true">Verbundene Auflagen anzeigen</a></p>
    </div>
    </div>
    </div>,
    <script>setEntityPicture("person", "{api:get-wikidata-id($person)}")</script>
    )
    else (<h1>[Diese Entität existiert nicht]</h1>)
};

declare function app:construct-idnos($idnos){
    for $idno in $idnos
    let $name := if (api:look-up-list("idno", $idno/data(@type))) then (api:look-up-list("idno", $idno/data(@type))) else ($idno/data(@type))
    let $linkPrefix := switch ($idno/data(@type))
        case "gnd" return "https://d-nb.info/gnd/"
        case "wikidata" return "https://www.wikidata.org/wiki/"
        case "viaf" return "https://viaf.org/viaf/"
        case "geonames" return "https://www.geonames.org/"
        case "d-bio" return "https://www.deutsche-biographie.de/"
        case "google-books" return "https://books.google.de/books?id="
        case "vd16" return "http://gateway-bayern.de/"
        case "vd17" return "https://kxp.k10plus.de/DB=1.28/CMD?MATCFILTER=N&amp;MATCSET=N&amp;ACT0=&amp;IKT0=&amp;TRM0=&amp;ACT3=*&amp;IKT3=8183&amp;ACT=SRCHA&amp;IKT=8079&amp;SRT=YOP&amp;ADI_BIB=&amp;TRM="
        case "vd18" return "https://kxp.k10plus.de/DB=1.65/SET=11/TTL=1/CMD?ACT=SRCHA&amp;IKT=8080&amp;TRM="
        case "bsb" return "https://opacplus.bsb-muenchen.de/metaopac/search?View=default&amp;id="
        case "K10plusPPN" return "https://opac.k10plus.de/DB=2.299/PPNSET?PPN="
        default return ""
    let $id := switch ($idno/data(@type))
        case "vd16" return replace($idno/text(), " ", "+")
        case "vd17" return tokenize($idno/text(), " ")[2]
        case "vd18" return replace($idno/text(), " ", "")
        default return $idno/text()
    let $linkSuffix := switch ($idno/data(@type))
        case "d-bio" return ".html"
        default return ""
    let $link := concat($linkPrefix, $id, $linkSuffix)
    return
        <li>{$name}: <a href="{$link}" target="_blank">{$idno/text()}</a></li>
};

declare function app:construct-sources($sources){
    let $sources := tokenize($sources)
    let $prefix := if (count($sources) > 1) then ("Quellen: ") else ("Quelle: ")
    let $list := app:list-with-commas(api:look-up-list('idno', $sources))
    return ($prefix, $list)
};

declare function app:wrap-in-toolbox($wordSequence, $sourcesSequence){
    for $word at $pos in $wordSequence return <span class="tooltipcontainer">{$word}<span class="tooltiptext">{app:construct-sources($sourcesSequence[$pos])}</span></span>
};


(:#########################:)
(:######## ORT PAGE #######:)
(:#########################:)

declare 
%templates:wrap
function app:show-place-page($node as node()*, $model as map(*), $id as xs:string){
    let $place := api:get-place-by-id($id)
    return
    if ($place) then (
    <div class="container">
    <div class="row d-flex justify-content-center">
    <div class="col col-lg-10 col-xl-8">
    <h3 id="entity-class"><i class="fas fa-map-marker-alt"/> Ort</h3>
    <p id="entity-id">{$id}</p>
    <h1>{if (api:get-place-name($place)) then (app:wrap-in-toolbox(api:get-place-name($place), api:get-place-name-sources($place))) else ("[Ohne Namen]")}</h1>
    <div class="row">   
    <div class="col col-md-8 col-12 order-last order-md-first">
    <h4>Daten:</h4>
    <ul>
        <li><span class="low-opacity">Namen im Katalog: </span>{if (api:get-place-addNames-from-catalog($place)) then (<span class="bold">{app:list-with-commas(api:get-place-addNames-from-catalog($place))}</span>) else ("[Ohne Namen]")}</li>
        <li><span class="low-opacity">Heutiges Land: </span>{if (api:get-country($place)) then (<span class="bold">{app:wrap-in-toolbox(api:get-country($place), api:get-country-sources($place))}</span>) else ("[Unbekannt]")}</li>
        <li><span class="low-opacity">Koordinaten: </span>{if (api:get-coordinates($place)) then (<span class="bold"><a href="{app:construct-opm-url(api:get-coordinates($place))}" target="_blank">{app:wrap-in-toolbox(api:get-coordinates($place), api:get-coordinates-sources($place))}</a></span>) else ("[Unbekannt]")}</li>
    </ul>
    {if (api:get-idnos($place)) then (<h4>Externe Ressourcen:</h4>,<ul>{app:construct-idnos(api:get-idnos($place))}</ul>) else()}
    </div>
    <div class="col col-md-4 col-12 order-first order-md-last" id="entity-image-col">
    <figure class="figure">
    <div id="entity-image-container">
    <img id="entity-image" src="../resources/images/fa_place.png" alt="Bild" class="figure-img"/>
    </div>
    <figcaption id="entity-image-caption" class="figure-caption text-center">Suche Bild...</figcaption>
    </figure>
    </div>
    </div>  
    <h4>Vorkommen im Katalog:</h4>
    <p>{if (app:construct-occurence-in-catalog($id)) then (<span class="low-opacity">[Auf Seiten:] </span>,app:construct-occurence-in-catalog($id)) else ("[Ohne Vorkommen]")}</p>
    <h4>Aktionen:</h4>
    <p><a href="datenbank.html?query=alleAuflagen&amp;edition_filterPubPlaceId={$id}&amp;resetCache=true">Verbundene Auflagen anzeigen</a></p>
    <p><a href="datenbank.html?query=allePersonen&amp;person_filterPlaceId={$id}&amp;resetCache=true">Verbundene Personen anzeigen</a></p>
    </div>
    </div>
    </div>,
    <script>setEntityPicture("place", "{api:get-wikidata-id($place)}")</script>
    )
    else (<h1>[Diese Entität existiert nicht]</h1>)
};

declare function app:construct-opm-url($coordinates){
    let $coordinates := tokenize($coordinates)
    let $lat := $coordinates[1]
    let $lon := $coordinates[2]
    return concat("http://www.openstreetmap.org/?mlat=", $lat, "&amp;mlon=", $lon, "&amp;zoom=6")
};



(:##################:)
(:##### HELPER #####:)
(:##################:)

declare function app:list-with-commas($inputSequence){
    if (count($inputSequence) < 2) then $inputSequence
    else
    for $item at $pos in $inputSequence
        return if ($pos != count($inputSequence)) then ($item, ", ") else $item
};

(: Ersetze das Elemente, wo die Funktion aufgerufen wurde durch Element mit jeweiliger CSS-Datei :)
declare function app:set-css($node as node()*, $model as map(*)){
    let $cssFile := $model?cssFile (:  Frage in $model den Wert von cssFile ab. Dafür muss ich in view.xql eine map anlegen und sie als Argument $content -> templates:apply() übergeben. :)
    return
    if  ($cssFile) then
    <link rel="stylesheet" type="text/css" href="{$model?cssFile}"/>
    else ()
};

declare function app:set-js($node as node()*, $model as map(*)){
    let $jsFile := $model?jsFile
    return
    if  ($jsFile) then
    <script type="text/javascript" src="{$model?jsFile}"/>
    else ()
};



