"""Build the approved public homepage and explicitly approved talk assets."""
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROJECT_FIELDS = {'id', 'title', 'context', 'career_id', 'layers', 'summary', 'brief', 'resources', 'collaborators'}
BRIEF_FIELDS = {'problem', 'role', 'challenge', 'approach'}
PROJECT_PREVIEWS = {
    'review-analytics': ('assets/projects/review-widget.png','Review widgets installed in storefronts','Storefront review widget',3468,1212),
    'reviewro': ('assets/projects/reviewro-app.png','REVIEWRO app screens','Product discovery and review exploration',2190,1145),
}

TALK_ASSETS = {'assets/talks/sk-ai-summit-2024-video.jpg', 'assets/talks/seoultech-2021-cover.png', 'assets/talks/seoultech-2021.pdf'}


def talk_url(value):
    return esc(value) if value in TALK_ASSETS else safe_url(value)


def esc(value):
    return html.escape(str(value), quote=True)


def safe_url(value):
    parsed = urlparse(value)
    if any(c.isspace() for c in value):
        raise ValueError('Invalid URL')
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username:
        return esc(value)
    if parsed.scheme == 'mailto' and re.fullmatch(r'[^\s<>@]+@[^\s<>@]+', parsed.path):
        return esc(value)
    raise ValueError('Unsupported URL')


def origin(value):
    safe_url(value)
    parsed = urlparse(value)
    if parsed.scheme != 'https' or parsed.path not in ('', '/') or parsed.query or parsed.fragment or not re.fullmatch(r'[A-Za-z0-9.-]+(?::\d+)?', parsed.netloc):
        raise ValueError('Expected HTTPS origin')
    return f'https://{parsed.netloc}'


def template(name, values):
    source = (ROOT / 'src' / name).read_text()
    return re.sub(r'\{\{([a-z_]+)\}\}', lambda match: values[match.group(1)], source)


def action(url, label, external=False):
    target = ' target="_blank" rel="noopener noreferrer"' if external else ''
    path = 'M14 3h7v7M21 3L10 14M10 3H4a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1v-6' if external else 'M9 5l7 7-7 7'
    icon = f'<svg class="action-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="{path}"/></svg>'
    return f'<a class="button button-outline" href="{safe_url(url) if external else esc(url)}"{target}><span>{esc(label)}</span>{icon}</a>'


def bullets(items, css=''):
    return f'<ul class="{css}">' + ''.join(f'<li>{esc(item)}</li>' for item in items) + '</ul>'


def validate(data):
    allowed = {'name','role','headline','intro','bio','site_url','links','career','layers','publications','education','for_fun','analytics','projects','talks'}
    if set(data) - allowed:
        raise ValueError('Unapproved content fields')
    ids = set()
    for project in data['projects']:
        if set(project) != PROJECT_FIELDS:
            raise ValueError('Only approved public project summary fields are allowed')
        if project['collaborators'] != sorted(set(project['collaborators'])) or any(not isinstance(name,str) or not name.strip() for name in project['collaborators']):
            raise ValueError('Collaborator names must be unique and sorted')
        for resource in project['resources']:
            if set(resource) != {'label','url'}:
                raise ValueError('Only public resource labels and URLs are allowed')
            safe_url(resource['url'])
        if set(project['brief']) != BRIEF_FIELDS or any(not isinstance(v, str) or not v.strip() or len(v) > 240 for v in project['brief'].values()):
            raise ValueError('Project briefs require four concise public summary fields')
        if not re.fullmatch('[a-z][a-z0-9-]*', project['id']) or project['id'] in ids:
            raise ValueError('Invalid project ID')
        ids.add(project['id'])
    encoded = json.dumps(data)
    if any(value in encoded for value in ['drive.google.com', 'docs.google.com', '/images/', 'data:image/']):
        raise ValueError('Private source material must not enter public content')


def base(data, prefix='', title=None, route=''):
    files = ['style.css', 'site.js']
    version = hashlib.sha256(b''.join((ROOT / 'assets' / name).read_bytes() for name in files)).hexdigest()[:12]
    policy = "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' https://skillicons.dev; connect-src 'none'; base-uri 'none'; form-action 'none'"
    return {'name':esc(data['name']), 'prefix':prefix, 'title':esc(title or f'{data["name"]} | AI service developer'),
            'site_url':safe_url(data['site_url']+route), 'version':version, 'policy':esc(policy),
            'site_header':template('header.html',{'prefix':prefix,'fun_link':f'<a href="{prefix}#for-fun">For fun</a>' if data.get('for_fun') else ''})}


def cards(data):
    result=[]
    for p in data['projects']:
        brief=''.join(f'<div><dt>{label}</dt><dd>{esc(p["brief"][key])}</dd></div>' for key,label in [('problem','Problem'),('role','My role'),('challenge','Challenge'),('approach','Approach')])
        talk_link='<p class="project-talk"><a href="../#talks">SK AI Summit 2024 · Talk &amp; recording</a></p>' if p['id']=='counseling-search' else ''
        resources='<div class="resource-links">'+''.join(action(r['url'],r['label'],True) for r in p['resources'])+'</div>' if p['resources'] else ''
        media=''
        if p['id'] in PROJECT_PREVIEWS:
            src,alt,caption,width,height=PROJECT_PREVIEWS[p['id']]
            media=f'<figure class="project-list-preview"><img src="../{src}" alt="{esc(alt)}" width="{width}" height="{height}" loading="lazy" decoding="async"><figcaption>{esc(caption)}</figcaption></figure>'
        affiliation='<span class="collaborator-affiliation">SK Telecom colleagues</span>' if p['career_id'].startswith('skt-') else ''
        others='<span class="collaborator-others"> 외</span>' if p['id'] in {'reviewro','review-analytics'} else ''
        people='<div class="project-collaborators"><span class="collaborator-with">with</span> <ul aria-label="Project collaborators">'+' '.join(f'<li>{esc(name)}</li>' for name in p['collaborators'])+'</ul>'+others+affiliation+'</div>' if p['collaborators'] else ''
        result.append(f'<article class="project" id="project-{p["id"]}"><h3>{esc(p["title"])}</h3>{people}{media}<p>{esc(p["summary"])}</p><dl class="project-brief">{brief}</dl>{talk_link}{resources}</article>')
    return '<div class="project-grid">'+''.join(result)+'</div>'


def talk_card(p):
    media=p.get('media');preview=''
    if media:
        if media['src'] not in TALK_ASSETS:
            raise ValueError('Unapproved talk media')
        play='<span class="play-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M9 5v14l11-7z"/></svg></span>' if media['kind']=='video' else ''
        preview=f'<a class="talk-preview" href="{talk_url(media["url"])}"><span class="talk-image"><img src="{esc(media["src"])}" alt="" loading="lazy" width="480" height="270">{play}</span><span class="talk-caption">{esc(media["label"])}</span></a>'
    links=''.join(action(r['url'],r['label'],True) for r in p['links'])
    return f'<article class="talk-row"><span class="period">{esc(p["date"])}</span><div><h3>{esc(p["title"])}</h3><p class="job-role">{esc(p["venue"])}</p>{preview}<div class="resource-links">{links}</div></div></article>'


def fun(data):
    return ''.join(f'<article class="project"><h3><a href="{safe_url(p["url"])}">{esc(p["title"])}</a></h3><p>{esc(p["summary"])}</p></article>' for p in data.get('for_fun',[])) or '<p class="empty-state">No public experiments yet.</p>'


def render(data):
    validate(data)
    values = base(data)
    values.update({key:esc(data[key]) for key in ['headline','intro']})
    values['bio'] = bullets(data['bio'],'bio-bullets')
    icons = {'GitHub':'github','LinkedIn':'linkedin','Blog':'blog'}
    values['links'] = ''.join(f'<a href="{safe_url(p["url"])}"><img class="contact-icon" src="assets/icons/{icons[p["label"]]}.svg" alt="" width="16" height="16"><span>{esc(p["label"])}</span></a>' for p in data['links'])
    career=[]
    for job in data['career']:
        projects=[p for p in data['projects'] if p['career_id']==job['id']]
        related=''.join(f'<div class="career-project"><h4><a href="projects/#project-{p["id"]}">{esc(p["title"])}</a></h4><p>{esc(p["summary"])}</p></div>' for p in projects)
        logo={'skt-current':'skt.png','skt-previous':'skt.png','hyundai':'hyundai.png','lg':'lg.jpg','tmax':'tmax.png'}.get(job['id'])
        image=f'<img class="company-logo" src="assets/companies/{logo}" alt="" width="36" height="36">' if logo else ''
        mark=f'<span class="company-avatar" aria-hidden="true">{image}</span>' if logo else ''
        career.append(f'<article class="timeline-row"><div class="period">{esc(job["period"])}</div><div><h3 class="company-name">{mark}<span>{esc(job["company"])}</span></h3><p class="job-role">{esc(job["role"])}</p>{bullets(job["bullets"],"career-bullets")}<p class="exact-date">{esc(job["dates"])}</p><div class="career-projects">{related}</div></div></article>')
    values['career']=''.join(career)
    values['fun_section']=f'<section id="for-fun" class="section"><h2>For fun</h2>{fun(data)}</section>' if data.get('for_fun') else ''
    values['papers']=''.join(f'<article class="paper"><span class="paper-year">{esc(p["year"])}</span><div><h3><a href="{safe_url(p["url"])}">{esc(p["title"])}</a></h3><p class="authors">{esc(p["authors"])}</p><p class="venue">{esc(p["venue"])}</p><details><summary>BibTeX</summary><pre><code>{esc(p["citation"])}</code></pre></details></div></article>' for p in data['publications'])
    degrees=[]
    for degree in data['education']:
        thesis=degree.get('thesis');link=f'<p class="thesis">Thesis: <a href="{safe_url(thesis["url"])}">{esc(thesis["title"])}</a></p>' if thesis else ''
        detail=f'<p>{esc(degree["detail"])}</p>' if degree.get('detail') else ''
        degrees.append(f'<article class="education-row"><span class="period">{esc(degree["period"])}</span><div><h3>{esc(degree["degree"])}</h3><p class="school">{esc(degree["school"])}</p>{detail}{link}</div></article>')
    values['education']=''.join(degrees)
    values['talks']=''.join(talk_card(p) for p in data['talks'])
    layers=[]
    for layer in data['layers']:
        skills=[]
        for skill in layer['skills']:
            icon=''
            if skill.get('icon'):
                if not re.fullmatch('[a-z0-9]+',skill['icon']):raise ValueError('Invalid icon')
                icon=f'<img src="https://skillicons.dev/icons?i={skill["icon"]}&amp;theme=light" alt="" width="24" height="24" loading="lazy">'
            skills.append(f'<span class="skill">{icon}<span>{esc(skill["name"])}</span></span>')
        layers.append(f'<article class="stack-layer"><h3>{esc(layer["name"])}</h3><div class="skills">{"".join(skills)}</div></article>')
    values['stack']=''.join(layers)
    return template('template.html',values)


FUN_FIELDS = {'id','title','tagline','summary','status','url','why','features','architecture','releases','posts'}
# Screens reused from already-published blog posts (same origin, self-hosted).
FUN_IMAGES = {
    'home': ('blog/media/noteon-good-lectures-with-notes/home.png', 1492, 2563),
    'lecture': ('blog/media/noteon-good-lectures-with-notes/lecture.png', 1492, 910),
    'notes': ('blog/media/noteon-good-lectures-with-notes/notes.png', 1280, 900),
    'architecture': ('assets/fun/noteon-architecture.png', 1200, 1024),
    'memo': ('assets/fun/noteon-memo.png', 880, 550),
    'study': ('assets/fun/noteon-study.png', 600, 370),
}


def load_fun():
    pages=[]
    for path in sorted((ROOT/'content/fun').glob('*.json')):
        page=json.loads(path.read_text())
        if set(page)!=FUN_FIELDS or not re.fullmatch('[a-z][a-z0-9-]*',page['id']):
            raise ValueError('Unapproved For fun fields')
        safe_url(page['url'])
        for post in page['posts']:
            if not post['url'].startswith('/blog/'):safe_url(post['url'])
        pages.append(page)
    return pages


def fun_cards(pages):
    if not pages:return ''
    def preview(p):
        src,w,h=FUN_IMAGES['lecture']
        return (f'<a class="fun-card-shot" href="fun/{p["id"]}/" aria-hidden="true" tabindex="-1">'
                f'<img src="../{src}" alt="" width="{w}" height="{h}" loading="lazy" decoding="async"></a>')
    items=''.join(f'<article class="project fun-card" id="fun-{p["id"]}"><div class="fun-card-text"><p class="project-context">{esc(p["status"])}</p><h3><a href="fun/{p["id"]}/">{esc(p["title"])}</a></h3><p>{esc(p["summary"])}</p><div class="resource-links">{action("fun/"+p["id"]+"/","About "+p["title"])}{action(p["url"],"Open "+p["title"],True)}</div></div>{preview(p)}</article>' for p in pages)
    return f'<section class="projects-group" id="for-fun" aria-labelledby="for-fun-title"><h2 id="for-fun-title">For fun</h2><p class="group-lede">Side projects I build for myself.</p>{items}</section>'


def render_projects(data, fun_pages=()):
    validate(data)
    values=base(data,prefix='../',title=f'{data["name"]} | Projects',route='projects/')
    work=cards(data)
    if fun_pages:
        tabs=(f'<nav class="project-tabs" aria-label="Project categories">'
              f'<a href="#work"><span>Work</span><span class="tab-count">{len(data["projects"])}</span></a>'
              f'<a href="#for-fun"><span>For fun</span><span class="tab-count">{len(fun_pages)}</span></a></nav>')
        values['projects']=tabs+f'<section class="projects-group" id="work" aria-labelledby="work-title"><h2 id="work-title">Work</h2><p class="group-lede">Services I planned and built at work.</p>{work}</section>'+fun_cards(fun_pages)
    else:
        values['projects']=work
    return template('projects.html',values)


def render_fun(data, page):
    prefix='../../../'
    values=base(data,prefix=prefix,title=f'{page["title"]} | {data["name"]}',route=f'projects/fun/{page["id"]}/')
    values['description']=esc(page['summary'])
    def img(key, alt, cls=''):
        src,w,h=FUN_IMAGES[key]
        return f'<img class="{cls}" src="{prefix}{src}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async">'
    paras=lambda items:''.join(f'<p>{esc(t)}</p>' for t in items)
    nav='<nav class="fun-toc" aria-label="On this page"><a href="#why">Why</a><a href="#features">Features</a><a href="#architecture">Architecture</a><a href="#releases">Release notes</a></nav>'
    posts=''.join(action(prefix+p['url'].lstrip('/') if p['url'].startswith('/blog/') else p['url'],p['label'],not p['url'].startswith('/blog/')) for p in page['posts'])
    hero=(f'<header class="fun-hero"><p class="fun-crumb"><a href="../../">Projects</a> / <a href="../../#for-fun">For fun</a></p>'
          f'<h1>{esc(page["title"])}</h1><p class="fun-tagline">{esc(page["tagline"])}</p><p class="fun-summary">{esc(page["summary"])}</p>'
          f'<p class="project-context">{esc(page["status"])}</p><div class="resource-links">{action(page["url"],"Open "+page["title"],True)}{posts}</div>'
          f'<figure class="fun-shot fun-shot-hero">{img("lecture","NoteOn lecture screen: player on the left, timed key segments on the right")}</figure></header>')
    why=(f'<section class="section" id="why"><h2>Why I built it</h2><div class="fun-two"><div><h3>The problem</h3>{paras(page["why"]["problem"])}</div>'
         f'<div><h3>The motivation</h3>{paras(page["why"]["motivation"])}</div></div></section>')
    feats=[]
    for f in page['features']:
        shot=f'<figure class="fun-shot">{img(f["image"],f["title"]+" screen")}</figure>' if f.get('image') else ''
        feats.append(f'<article class="fun-feature{" has-shot" if shot else ""}"><div><h3>{esc(f["title"])}</h3><p>{esc(f["text"])}</p></div>{shot}</article>')
    features=f'<section class="section" id="features"><h2>Features</h2>{"".join(feats)}</section>'
    architecture=(f'<section class="section" id="architecture"><h2>Architecture</h2>'
                  f'<figure class="fun-shot fun-shot-wide">{img("architecture","How NoteOn fits together: frontend, backend, data and processing, the curation pipeline, and cross-cutting logging, security and monitoring, with the main calls between them")}<figcaption>How the parts connect. Numbered arrows are the main calls.</figcaption></figure>'
                  '</section>')
    rel=''.join(f'<article class="timeline-row"><div class="period">{esc(r["date"])}</div><div>{bullets(r["items"],"career-bullets")}</div></article>' for r in page['releases'])
    releases=f'<section class="section" id="releases"><h2>Recent release notes</h2>{rel}</section>'
    values['body']=hero+nav+why+features+architecture+releases
    return template('fun.html',values)


def crawl_files(site_url):
    """sitemap.xml and robots.txt for the public routes only: home, Projects index, Blog index and posts."""
    base = site_url.rstrip('/')
    urls = [(f'{base}/', None), (f'{base}/projects/', None), (f'{base}/blog/', None)]
    for page in load_fun():urls.append((f'{base}/projects/fun/{page["id"]}/', None))
    for post in sorted((ROOT/'blog/src/posts').glob('*.md')):
        date = re.search(r'^date:\s*"(\d{4}-\d{2}-\d{2})', post.read_text(), re.M)
        urls.append((f'{base}/blog/{post.stem}/', date.group(1) if date else None))
    entries = ''.join(
        f'  <url><loc>{html.escape(loc)}</loc>' + (f'<lastmod>{lastmod}</lastmod>' if lastmod else '') + '</url>\n'
        for loc, lastmod in urls)
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + entries + '</urlset>\n')
    robots = f'User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n'
    return sitemap, robots


def main():
    data=json.loads((ROOT/'content/profile.json').read_text());validate(data)
    blog = ROOT / 'blog'
    subprocess.run(['npm', 'run', 'build'], cwd=blog, check=True)
    output=ROOT/'dist'
    if output.exists():shutil.rmtree(output)
    output.mkdir();(output/'index.html').write_text(render(data))
    (output/'projects').mkdir()
    fun_pages=load_fun()
    (output/'projects/index.html').write_text(render_projects(data,fun_pages))
    for page in fun_pages:
        target=output/'projects/fun'/page['id'];target.mkdir(parents=True)
        (target/'index.html').write_text(render_fun(data,page))
    shutil.copytree(blog / 'dist', output / 'blog')
    shutil.copytree(ROOT/'assets',output/'assets')
    (output/'.nojekyll').touch()
    sitemap, robots = crawl_files(data['site_url'])
    (output/'sitemap.xml').write_text(sitemap)
    (output/'robots.txt').write_text(robots)
    (output/'404.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Page not found</title><h1>Page not found</h1><a href="/">Home</a></html>')
    print('Built the public homepage, Projects summary index, and Blog.')


if __name__=='__main__':main()
