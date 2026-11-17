$-- kinyonga letter. A letter has no title block and no contents, so this does not call Quarto's `article()`.
$--
$-- The function is defined here, not in a template partial, because this file lands after the brand block of the
$-- generated document: `brand-color` is a dictionary of the brand palette, so no hex value is written twice.
$-- Quarto emits the body itself after this partial; the show rule below receives it as `doc`.
#let kn-letter(
  sender: (),
  recipient: (),
  contact: (),
  date: none,
  subject: none,
  closing: [Yours sincerely,],
  signatory: none,
  doc,
) = {
  let blue = brand-color.at("blue", default: brand-color.at("primary", default: rgb("#0369A1")))
  let ink = brand-color.at("foreground", default: luma(30))
  let slate = brand-color.at("slate", default: luma(110))
  let rule = brand-color.at("rule", default: luma(226))
  set page(
    paper: "a4",
    margin: (top: 3.4cm, bottom: 2.6cm, x: 2.4cm),
    numbering: none,
    background: place(top + left, rect(width: 100%, height: 0.5cm, fill: blue, stroke: none)),
    footer: if contact.len() > 0 { align(center, text(size: 8pt, fill: slate, contact.join([  ·  ]))) },
  )
  set par(justify: false, leading: 0.7em)
  set text(font: $if(brand.typography.base.family)$$brand.typography.base.family$$else$"Libre Franklin"$endif$, size: 10.5pt, fill: ink)
  show link: set text(fill: blue)
  grid(
    columns: (1fr, 1fr),
    gutter: 1cm,
    [
      #for line in recipient [#line \ ]
    ],
    align(right, text(fill: slate, size: 9.5pt)[
      #for line in sender [#line \ ]
    ]),
  )
  v(1.2cm)
  if date != none { align(right, text(fill: slate, date)) }
  v(0.6cm)
  if subject != none {
    text(font: $if(brand.typography.headings.family)$$brand.typography.headings.family$$else$"Jost"$endif$, weight: 600, size: 13pt, fill: blue, subject)
    v(0.2cm)
    line(length: 100%, stroke: 0.6pt + rule)
    v(0.5cm)
  }
  doc
  v(1cm)
  closing
  v(1.4cm)
  if signatory != none { strong(signatory) }
}

#show: doc => kn-letter(
  $if(sender-address)$
  sender: ($for(sender-address)$[$sender-address$], $endfor$),
  $else$
  sender: ($if(by-author)$[$for(by-author)$$it.name.literal$$sep$, $endfor$], $endif$$if(identity.location)$[$identity.location$], $endif$),
  $endif$
  recipient: ($for(recipient)$[$recipient$], $endfor$),
  contact: ($if(identity.email)$[$identity.email$], $endif$$if(identity.phone)$[$identity.phone$], $endif$$if(identity.url)$[$identity.url$], $endif$),
  $if(date)$date: [$date$],$endif$
  $if(subject)$subject: [$subject$],$endif$
  $if(closing)$closing: [$closing$],$endif$
  $if(by-author)$signatory: [$for(by-author)$$it.name.literal$$sep$, $endfor$],$endif$
  doc,
)
