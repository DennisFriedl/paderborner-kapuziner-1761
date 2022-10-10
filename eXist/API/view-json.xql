xquery version "3.1" encoding "UTF-8";

declare namespace output = "http://www.w3.org/2010/xslt-xquery-serialization";
import module namespace api = "http://API/templates" at "app.xql";

declare namespace tei = "http://www.tei-c.org/ns/1.0";

import module namespace console = "http://exist-db.org/xquery/console";


declare option output:method "json";
declare option output:media-type "application/json";



let $entity_type := request:get-parameter("entityType", "")
return
    (: PERSONEN :)
    if ($entity_type = "persons") then
        (
        for $person in api:get-all-persons()
        return
            (:
            
            :)
            map {
                "id": $person/data(@xml:id),
                "name": $person/tei:persName/normalize-space(tei:name),
                "geschlecht": $person/tei:sex/data(@value),
                "geburtsort_id": $person/tei:birth/tei:placeName/data(@key),
                "geburtsjahr_min": map:get(api:get-birth-date-range($person), "min_date"),
                "geburtsjahr_max": map:get(api:get-birth-date-range($person), "max_date"),
                "sterbeort_id": $person/tei:death/tei:placeName/data(@key),
                "sterbejahr_min": map:get(api:get-death-date-range($person), "min_date"),
                "sterbejahr_max": map:get(api:get-death-date-range($person), "max_date"),
                "organisation_id": $person/tei:affiliation/tei:orgName/data(@key),
                "glaube": for $faith in $person/tei:faith return normalize-space($faith)
            })

    (: ORTE :)
    else if ($entity_type = "places") then
        (
        for $place in api:get-all-places()
        return
            (:
                
            :)
            map {
                "id": $place/data(@xml:id),
                "name": $place/tei:placeName/normalize-space(tei:name),
                "koordinaten_lat": tokenize($place/tei:location/normalize-space(tei:geo))[1],
                "koordinaten_lon": tokenize($place/tei:location/normalize-space(tei:geo))[2],
                "land": $place/normalize-space(tei:country)
            })
            
    (: ORGANISATIONEN :)
    else if ($entity_type = "organisations") then
        (
        for $org in api:get-all-organisations()
        return
            map {
                "id": $org/data(@xml:id),
                "name": $org/tei:orgName/normalize-space(tei:name)
            })
            
            
     else if ($entity_type = "books") then
        (
        (: Ich mache das jetzt so, dass ich nicht bei jedem Buch genau bestimme, ob es später hinzugekommen ist oder entfernt wurde. Wenn es im Katalog zwei Exemplare gibt: Eines ist alt, wurde aber später entfernt und das andere wurde neu hinzugefügt, könnte es sein, dass der erste Eintrag sowohl auf hinzugefügt als auch auf entfernt steht, der Einfachheit halber. D.h. dass ich immer noch zwischen hinzugefügten und entfernten in der Statistik entscheiden kann, aber nicht die Aussage treffen kann, wann ein Buch sowohl hinzugefügt als auch entfernt wurde.:)
        for $edition in api:get-all-editions()
        for $hit_in_catalog in $api:kapuziner_pb//tei:rs[@type='edition' and @key=$edition/@xml:id]
        let $highest_measure := if ($hit_in_catalog/ancestor::tei:cell//tei:measure[@type='duplicate']) then (xs:integer(max($hit_in_catalog/ancestor::tei:cell//tei:measure[@type='duplicate']/data(@quantity)))) else (1)
        let $book_list := for $book in (1 to $highest_measure) return map{"später_hinzugefügt": 0, "später_entfernt": 0}
        
        (: Neu hinzugefügte Exemplare :)
        let $number_of_duplicates_with_hand := if ($hit_in_catalog/ancestor::tei:cell//tei:measure[@type='duplicate' and (@hand='#hand2' or @hand='#hand3' or parent::tei:add[@hand='#hand2' or @hand='#hand3'])]/data(@quantity)) then xs:integer(($hit_in_catalog/ancestor::tei:cell//tei:measure[@type='duplicate' and (@hand='#hand2' or @hand='#hand3' or parent::tei:add[@hand='#hand2' or @hand='#hand3'])]/data(@quantity)) - 1) else (0)
        let $number_of_duplicates_without_hand := if ($hit_in_catalog/ancestor::tei:cell//tei:measure[@type='duplicate' and not(@hand='#hand2' or @hand='#hand3') and not(ancestor::tei:add[@hand='#hand2' or @hand='#hand3'])]/data(@quantity)) then xs:integer(($hit_in_catalog/ancestor::tei:cell//tei:measure[@type='duplicate' and not(@hand='#hand2' or @hand='#hand3') and not(ancestor::tei:add[@hand='#hand2' or @hand='#hand3'])]/data(@quantity)) - 1) else (0)
        let $number_of_newly_added := if ($number_of_duplicates_with_hand gt 0) then ($number_of_duplicates_with_hand - $number_of_duplicates_without_hand) else (0)
        let $book_list := for $book at $pos in $book_list return if ($pos le $number_of_newly_added) then (map:put($book, "später_hinzugefügt", 1)) else ($book)
        
        (: Alle Bücher später hinzugefügt :)
        let $book_list := for $book in $book_list return if ($hit_in_catalog[ancestor::*[not(self::tei:del) and not(self::tei:subst) and (@hand='#hand2' or @hand='#hand3')]]) then (map:put($book, "später_hinzugefügt", 1)) else ($book)
        
        (: Entfernte Exemplare :)
        let $number_of_losses := if ($hit_in_catalog/ancestor::tei:cell//tei:measure[@type='loss']/data(@quantity)) then (xs:integer($hit_in_catalog/ancestor::tei:cell//tei:measure[@type='loss']/data(@quantity))) else (0)
        let $book_list := for $book at $pos in $book_list return if ($pos le $number_of_losses) then (map:put($book, "später_entfernt", 1)) else ($book)
        
        (: Alle Bücher entfernt :)
        let $book_list := for $book in $book_list return if ($hit_in_catalog[ancestor::tei:del]) then (map:put($book, "später_entfernt", 1)) else ($book)
        
        for $book in $book_list
        return
        (:
                
        :)
            map {
                "id": $edition/data(@xml:id),
                "m_id": api:get-monograph-from-edition($edition)/data(@xml:id),
                "s_id": api:get-series-from-monograph(api:get-monograph-from-edition($edition))/data(@xml:id),
                "authoren_ids": api:get-authors-ids(api:get-monograph-from-edition($edition)),
                "sprachen": api:get-all-languages(api:get-monograph-from-edition($edition)),
                "erscheinungsorte_ids": api:get-places-ids($edition),
                "erscheinungsjahr": api:get-date($edition),
                "format": api:get-dimensions($edition),
                "kategorie": api:get-category-from-pageNumber(api:get-pageNumber-of-entity(api:get-first-occurence-in-catalog($edition))),
                "später_hinzugefügt": map:get($book, "später_hinzugefügt"),
                "später_entfernt": map:get($book, "später_entfernt")
            }
            (: "position_in_kategorie": api:get-position-in-category($edition) Falls ichs brauche, muss ich es umschreiben, funktioniert noch mit den alten Kategoiren, die nicht zwischen drei O's unterscheiden :)
            )
            
      (: SPACE :)
      else if ($entity_type = "space") then
      (
        for $space in $api:kapuziner_pb//tei:space
        return
        (:

        :)
            map {
                "space_in_mm" : $space/data(@quantity),
                "kategorie": api:get-category-from-pageNumber(api:get-pageNumber-of-entity($space))
            }
      )
    
    else
        ()
