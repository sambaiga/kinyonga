$-- kinyonga CV. The CV has no title block and no contents, so this does not call Quarto's `article()`; the filter
$-- writes the name, the contact line and every section into the body.
$--
$-- Everything here is a `set` or `show` rule that keeps the element itself (the heading stays a heading), so the
$-- PDF keeps its tags: Typst 0.14 and later tag the structure by default.
#let kn-head = $if(brand.typography.headings.family)$$brand.typography.headings.family$$else$("Jost",)$endif$
#let kn-body = $if(brand.typography.base.family)$$brand.typography.base.family$$else$("Libre Franklin",)$endif$
#let kn-rule = brand-color.at("rule", default: luma(226))

$if(title)$
#set document(title: [$title$]$if(by-author)$, author: ($for(by-author)$"$it.name.literal$"$sep$, $endfor$)$endif$)
$endif$
$-- The brand logo is placed on every page by default; a CV keeps its first page free of images that carry no text.
#set page(paper: "a4", margin: (x: 1.7cm, y: 1.5cm), numbering: none, background: none)
#set text(font: kn-body, size: 9.5pt, lang: "$if(lang)$$lang$$else$en$endif$", hyphenate: false, features: (liga: 0, clig: 0), fill: brand-color.foreground)
#set par(justify: false, leading: 0.55em, spacing: 0.55em)
#set list(indent: 0.2em, body-indent: 0.55em, spacing: 0.4em)
#show link: set text(fill: brand-color.primary)
#show heading.where(level: 1): it => {
  set block(above: 0.5cm, below: 0.2cm)
  set text(font: kn-head, weight: "semibold", size: 11.5pt, fill: brand-color.primary)
  it
  v(-0.15cm)
  line(length: 100%, stroke: 0.6pt + kn-rule)
}
