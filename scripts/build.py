"""Build only the approved public profile, collections, and statistics page."""
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PROJECT_FIELDS = {'id', 'title', 'context', 'career_id', 'layers', 'summary'}


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
        if not re.fullmatch('[a-z][a-z0-9-]*', project['id']) or project['id'] in ids:
            raise ValueError('Invalid project ID')
        ids.add(project['id'])
    encoded = json.dumps(data)
    if any(value in encoded for value in ['drive.google.com', 'docs.google.com', '/images/', 'data:image/']):
        raise ValueError('Private source material must not enter public content')


def base(data, prefix='', title=None, route=''):
    files = ['style.css', 'site.js', 'analytics.js', 'stats.css', 'stats.js', 'stats-story.js']
    version = hashlib.sha256(b''.join((ROOT / 'assets' / name).read_bytes() for name in files)).hexdigest()[:12]
    endpoint = origin(data['analytics']['endpoint'])
    policy = f"default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' https://skillicons.dev; connect-src {endpoint}; base-uri 'none'; form-action 'none'"
    return {'name':esc(data['name']), 'prefix':prefix, 'title':esc(title or f'{data["name"]} | AI service developer'),
            'site_url':safe_url(data['site_url']+route), 'version':version, 'policy':esc(policy),
            'analytics_endpoint':esc(endpoint), 'production_host':esc(data['analytics']['production_host']),
            'site_header':template('header.html',{'prefix':prefix})}


def cards(data):
    return '<div class="project-grid">' + ''.join(f'<article class="project" id="project-{p["id"]}"><p class="project-context">{esc(p["context"])}</p><h3>{esc(p["title"])}</h3><p>{esc(p["summary"])}</p></article>' for p in data['projects']) + '</div>'


def fun(data):
    return ''.join(f'<article class="project"><h3><a href="{safe_url(p["url"])}">{esc(p["title"])}</a></h3><p>{esc(p["summary"])}</p></article>' for p in data.get('for_fun',[])) or '<p class="empty-state">No public experiments yet.</p>'


def render(data):
    validate(data)
    values = base(data)
    values.update({key:esc(data[key]) for key in ['headline','intro']})
    values['bio'] = bullets(data['bio'],'bio-bullets')
    icons = {'Email':'email','GitHub':'github','LinkedIn':'linkedin','Blog':'blog'}
    values['links'] = ''.join(f'<a href="{safe_url(p["url"])}"><img class="contact-icon" src="assets/icons/{icons[p["label"]]}.svg" alt="" width="16" height="16"><span>{esc(p["label"])}</span></a>' for p in data['links'])
    career=[]
    for job in data['career']:
        related=''.join(f'<div class="career-project"><h4><a href="#project-{p["id"]}">{esc(p["title"])}</a></h4><p>{esc(p["summary"])}</p></div>' for p in data['projects'] if p['career_id']==job['id'])
        career.append(f'<article class="timeline-row"><div class="period">{esc(job["period"])}</div><div><h3>{esc(job["company"])}</h3><p class="job-role">{esc(job["role"])}</p>{bullets(job["bullets"],"career-bullets")}<p class="exact-date">{esc(job["dates"])}</p><div class="career-projects">{related}</div></div></article>')
    values['career']=''.join(career);values['projects']=cards(data);values['fun']=fun(data)
    values['projects_action']=action('projects/','All projects')
    values['papers']=''.join(f'<article class="paper"><span class="paper-year">{esc(p["year"])}</span><div><h3><a href="{safe_url(p["url"])}">{esc(p["title"])}</a></h3><p class="authors">{esc(p["authors"])}</p><p class="venue">{esc(p["venue"])}</p><details><summary>BibTeX</summary><pre><code>{esc(p["citation"])}</code></pre></details></div></article>' for p in data['publications'])
    degrees=[]
    for degree in data['education']:
        thesis=degree.get('thesis');link=f'<p class="thesis">Thesis: <a href="{safe_url(thesis["url"])}">{esc(thesis["title"])}</a></p>' if thesis else ''
        detail=f'<p>{esc(degree["detail"])}</p>' if degree.get('detail') else ''
        degrees.append(f'<article class="education-row"><span class="period">{esc(degree["period"])}</span><div><h3>{esc(degree["degree"])}</h3><p class="school">{esc(degree["school"])}</p>{detail}{link}</div></article>')
    values['education']=''.join(degrees)
    values['talks']=''.join(f'<article class="talk-row"><span class="period">{esc(p["date"])}</span><div><h3>{esc(p["title"])}</h3><p class="job-role">{esc(p["venue"])}</p><div class="resource-links">{"".join(action(r["url"],r["label"],True) for r in p["links"])}</div></div></article>' for p in data['talks'])
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


def render_collection(data,kind):
    values=base(data,'../',f'{"Projects" if kind=="projects" else "For fun"} | {data["name"]}',kind+'/')
    values.update(heading='Projects' if kind=='projects' else 'For fun',description='Public projects and experiments by '+esc(data['name']),cards=cards(data) if kind=='projects' else fun(data))
    return template('collection.html',values)


def main():
    data=json.loads((ROOT/'content/profile.json').read_text());validate(data)
    output=ROOT/'dist'
    if output.exists():shutil.rmtree(output)
    output.mkdir();(output/'index.html').write_text(render(data))
    for kind in ['projects','for-fun']:
        (output/kind).mkdir();(output/kind/'index.html').write_text(render_collection(data,kind))
    (output/'stats').mkdir();(output/'stats/index.html').write_text(template('stats.html',base(data,'../',f'Site pulse | {data["name"]}','stats/')))
    shutil.copytree(ROOT/'assets',output/'assets')
    (output/'.nojekyll').touch()
    (output/'404.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Page not found</title><h1>Page not found</h1><a href="/">Home</a></html>')
    print('Built approved public summaries, For fun, and Site pulse. No detail pages are generated.')


if __name__=='__main__':main()
