-- kinyonga CV filter: builds the CV from `cv` (cv.yml) and `identity` (profile.yml) for Typst and HTML.
--
-- The whole body is plain Pandoc blocks, so there is one reading order and one text for both formats. Only the
-- right-aligned dates and the icons need a raw fragment, and none of them carries text. ATS rules kept here:
-- typographic dashes and soft hyphens are normalised, labels are real text, icons are images with no alt text and
-- are left out when `ats: true`.

local ATS = false

local function str(value)
  return pandoc.utils.stringify(value)
end

local function present(value)
  return value ~= nil and str(value) ~= ''
end

local function inlines(value)
  local kind = pandoc.utils.type(value)
  if kind == 'Inlines' then return value end
  if kind == 'Blocks' then return pandoc.utils.blocks_to_inlines(value) end
  return pandoc.Inlines({ pandoc.Str(str(value)) })
end

local function raw(typst, html)
  if FORMAT:match('typst') then return pandoc.RawInline('typst', typst) end
  if html == nil or html == '' then return pandoc.Str('') end
  return pandoc.RawInline('html', html)
end

local function fill(left_class)
  -- The gap between the left and right part of a line: flexible in Typst, a separator in ATS mode.
  if ATS then return pandoc.Str(' | ') end
  return raw('#h(1fr)', '')
end

local function line(parts)
  -- A line with a left part, a flexible gap and a right part. Typst fills the gap with `#h(1fr)`; HTML puts the two
  -- parts in spans and spreads them with CSS (`.kn-line > p`).
  local left, right = parts[1], parts[3] or {}
  local content = pandoc.List({})
  if FORMAT:match('typst') then
    content:extend(left)
    content:extend(parts[2])
    content:extend(right)
  else
    content:insert(pandoc.Span(left, pandoc.Attr('', { 'kn-left' })))
    content:insert(pandoc.Span(right, pandoc.Attr('', { 'kn-right' })))
  end
  return pandoc.Div({ pandoc.Para(content) }, pandoc.Attr('', { 'kn-line' }))
end

local function accent(inline_list)
  if FORMAT:match('typst') then
    local out = pandoc.List({ pandoc.RawInline('typst', '#text(fill: brand-color.primary)[') })
    out:extend(inline_list)
    out:insert(pandoc.RawInline('typst', ']'))
    return out
  end
  return pandoc.List({ pandoc.Span(inline_list, pandoc.Attr('', { 'kn-org' })) })
end

local function section(id, title)
  return pandoc.Header(2, { pandoc.Str(title) }, pandoc.Attr(id))
end

local function icon(name)
  if ATS then return pandoc.List({}) end
  return pandoc.List({
    raw('#pdf.artifact(box(baseline: 15%, image("' .. name .. '.svg", height: 0.85em))) ',
        '<img class="kn-icon" src="' .. name .. '.svg" alt="" /> '),
  })
end

local function contact(identity)
  local items = {}
  local function add(label, icon_name, content)
    local part = pandoc.List({})
    if ATS then part:insert(pandoc.Str(label .. ': ')) else part:extend(icon(icon_name)) end
    part:extend(content)
    items[#items + 1] = part
  end
  if present(identity.email) then
    add('Email', 'envelope', { pandoc.Link(str(identity.email), 'mailto:' .. str(identity.email)) })
  end
  if present(identity.phone) then
    local digits = str(identity.phone):gsub('[^%d+]', '')
    add('Phone', 'telephone', { pandoc.Link(str(identity.phone), 'tel:' .. digits) })
  end
  if present(identity.location) then add('Location', 'geo-alt', { pandoc.Str(str(identity.location)) }) end
  if present(identity.url) then
    add('Website', 'globe', { pandoc.Link(str(identity.url), 'https://' .. str(identity.url)) })
  end
  if present(identity.linkedin) then
    local handle = str(identity.linkedin)
    add('LinkedIn', 'linkedin', { pandoc.Link('linkedin.com/in/' .. handle, 'https://linkedin.com/in/' .. handle) })
  end
  if present(identity.github) then
    local handle = str(identity.github)
    add('GitHub', 'github', { pandoc.Link('github.com/' .. handle, 'https://github.com/' .. handle) })
  end
  local out = pandoc.List({})
  for index, item in ipairs(items) do
    if index > 1 then out:insert(ATS and pandoc.Str(' | ') or raw('#h(1.1em)', ' ')) end
    -- One item never breaks across lines: a box in Typst, a nowrap span in HTML.
    if FORMAT:match('typst') then
      out:insert(pandoc.RawInline('typst', '#box['))
      out:extend(item)
      out:insert(pandoc.RawInline('typst', ']'))
    else
      out:insert(pandoc.Span(item, pandoc.Attr('', { 'kn-item' })))
    end
  end
  return pandoc.Div({ pandoc.Para(out) }, pandoc.Attr('', { 'kn-contact' }))
end

local function escape_html(text)
  return (text:gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;'))
end

local function header(name, headline)
  if FORMAT:match('typst') then
    return {
      pandoc.RawBlock('typst', '#block(above: 0pt, below: 0.15cm)[#text(font: kn-head, weight: "semibold", size: 22pt)['
        .. name:gsub('[%[%]#$@\\*_`<>]', '\\%0') .. ']]'),
      pandoc.RawBlock('typst', '#block(above: 0pt, below: 0.25cm)[#text(fill: brand-color.primary, size: 11pt)['
        .. headline:gsub('[%[%]#$@\\*_`<>]', '\\%0') .. ']]'),
    }
  end
  -- Raw HTML, not a Header: Pandoc would wrap the whole page in a section of the first level-1 heading.
  return {
    pandoc.RawBlock('html', '<h1 class="kn-name">' .. escape_html(name) .. '</h1>'),
    pandoc.RawBlock('html', '<p class="kn-headline">' .. escape_html(headline) .. '</p>'),
  }
end

local function dates(role)
  return str(role.start) .. '-' .. str(role['end'])
end

local function experience(cv)
  local blocks = pandoc.List({ section('experience', 'Experience') })
  for position, job in ipairs(cv.experience) do
    local org = pandoc.List({ pandoc.Strong(inlines(job.org)) })
    if position > 1 and FORMAT:match('typst') then blocks:insert(pandoc.RawBlock('typst', '#v(0.2cm)')) end
    if ATS then
      local text = pandoc.List({ pandoc.Strong(inlines(job.org)) })
      if present(job.location) then text:insert(pandoc.Str(', ' .. str(job.location))) end
      blocks:insert(pandoc.Para(text))
    else
      blocks:insert(line({ accent(org), { fill() }, present(job.location) and { pandoc.Str(str(job.location)) } or {} }))
    end
    for _, role in ipairs(job.roles) do
      local title = pandoc.List({ pandoc.Strong(inlines(role.title)) })
      if present(role.unit) then title:insert(pandoc.Str(', ' .. str(role.unit))) end
      if ATS then
        title:insert(pandoc.Str(' | ' .. dates(role)))
        blocks:insert(pandoc.Para(title))
      else
        blocks:insert(line({ title, { fill() }, { pandoc.Str(dates(role)) } }))
      end
      if present(role.summary) then blocks:insert(pandoc.Para(inlines(role.summary))) end
      if role.bullets ~= nil then
        local items = {}
        for _, bullet in ipairs(role.bullets) do items[#items + 1] = { pandoc.Plain(inlines(bullet)) } end
        blocks:insert(pandoc.BulletList(items))
      end
    end
  end
  return blocks
end

local function achievements(cv)
  local items = {}
  for _, entry in ipairs(cv.achievements) do
    local content = pandoc.List({ pandoc.Strong({ pandoc.Str(str(entry.label) .. ':') }), pandoc.Space() })
    content:extend(inlines(entry.text))
    items[#items + 1] = { pandoc.Plain(content) }
  end
  return { section('achievements', 'Key Achievements'), pandoc.BulletList(items) }
end

local function education(cv)
  local blocks = pandoc.List({ section('education', 'Education') })
  for _, entry in ipairs(cv.education) do
    local left = pandoc.List({ pandoc.Strong(inlines(entry.degree)), pandoc.Str(', ' .. str(entry.school)) })
    if present(entry.location) then left:insert(pandoc.Str(', ' .. str(entry.location))) end
    if ATS then
      left:insert(pandoc.Str(' | ' .. str(entry.year)))
      blocks:insert(pandoc.Para(left))
    else
      blocks:insert(line({ left, { fill() }, { pandoc.Str(str(entry.year)) } }))
    end
  end
  return blocks
end

local function skills(cv)
  local blocks = pandoc.List({ section('skills', 'Skills') })
  for _, entry in ipairs(cv.skills) do
    local names = {}
    for _, item in ipairs(entry.items) do names[#names + 1] = str(item) end
    blocks:insert(pandoc.Para({ pandoc.Strong({ pandoc.Str(str(entry.group) .. ':') }), pandoc.Space(),
      pandoc.Str(table.concat(names, ', ')) }))
  end
  return blocks
end

local function publications(cv)
  local items = {}
  for _, entry in ipairs(cv.publications) do items[#items + 1] = { pandoc.Plain(inlines(entry)) } end
  return { section('publications', 'Selected Publications'), pandoc.BulletList(items) }
end

local function normalise(blocks)
  -- Typographic dashes and soft hyphens become what an ATS reads: a hyphen and nothing.
  return pandoc.Pandoc(blocks):walk({
    Str = function(el)
      local text = el.text:gsub('\u{2013}', '-'):gsub('\u{2014}', '-'):gsub('\u{2212}', '-'):gsub('\u{00AD}', '')
      return pandoc.Str(text)
    end,
  }).blocks
end

function Pandoc(doc)
  local cv = doc.meta.cv
  if cv == nil then return nil end
  ATS = doc.meta.ats ~= nil and doc.meta.ats == true
  local identity = doc.meta.identity or {}
  local blocks = pandoc.List({})
  blocks:extend(header(str(doc.meta.title or ''), str(cv.headline or '')))
  blocks:insert(contact(identity))
  blocks:insert(section('summary', 'Professional Summary'))
  blocks:insert(pandoc.Para(inlines(cv.summary)))
  if cv.achievements ~= nil then blocks:extend(achievements(cv)) end
  if cv.experience ~= nil then blocks:extend(experience(cv)) end
  if cv.education ~= nil then blocks:extend(education(cv)) end
  if cv.skills ~= nil then blocks:extend(skills(cv)) end
  if cv.publications ~= nil then blocks:extend(publications(cv)) end
  blocks:extend(doc.blocks)
  doc.blocks = normalise(blocks)
  return doc
end
