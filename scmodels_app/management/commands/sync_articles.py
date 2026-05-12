"""
Django management command to sync WeChat articles from episodes_tracker.md to ModelEntry.

Usage:
    python manage.py sync_articles
    python manage.py sync_articles --dry-run
    python manage.py sync_articles --episode 6
"""

import json, re, os, random, math
from datetime import datetime
from pathlib import Path
from io import BytesIO

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFilter

from scmodels_app.models import ModelEntry, Tag

# ── Config ──
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_PATH = BASE_DIR / 'sync_config.json'
TRACKER_PATH = Path('/root/.hermes/cron/episodes_tracker.md')
SYNC_LOG_PATH = Path('/root/.hermes/cron/sync_log.json')
COVER_DIR = BASE_DIR / 'mediafiles' / 'models' / 'covers'

# Color palettes for different model types
PALETTES = {
    'foundation':    [(20, 50, 100), (30, 80, 150), (10, 40, 80), (50, 120, 200)],
    'geneformer':    [(80, 20, 60),  (120, 40, 100), (60, 10, 40),  (160, 60, 140)],
    'virtual_cell':  [(20, 80, 60),  (40, 140, 100), (15, 60, 40),  (60, 180, 140)],
    'perturbation':  [(100, 40, 20), (160, 60, 40),  (70, 30, 10),  (200, 80, 50)],
    'multimodal':    [(60, 30, 100), (100, 50, 160), (40, 20, 70),  (140, 80, 200)],
    'other':         [(40, 40, 60),  (70, 70, 100),  (30, 30, 45),  (100, 100, 140)],
}


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_sync_log():
    if SYNC_LOG_PATH.exists():
        with open(SYNC_LOG_PATH) as f:
            return json.load(f)
    return {"synced_episodes": [], "last_sync": None}


def save_sync_log(log):
    SYNC_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNC_LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


CRON_OUTPUT_DIR = Path('/root/.hermes/cron/output/a6f17b6045c9')
WORKSPACE_DIR = Path('/root/AI_workspace/单细胞大模型推文')


def extract_article_content(episode):
    """Extract full article markdown — prefer AI_workspace, fallback to cron outputs."""
    date_str = episode['date']
    ep_num = episode['number']
    
    # 1) Try AI_workspace first (clean article.md)
    if WORKSPACE_DIR.exists():
        for d in sorted(WORKSPACE_DIR.iterdir()):
            if not d.is_dir():
                continue
            # Match by date and episode number in directory name
            if date_str in d.name and f'第{ep_num}期' in d.name:
                af = d / 'article.md'
                if af.exists():
                    text = af.read_text()
                    # Extract body: everything after the first "---" separator
                    parts = text.split('---', 1)
                    if len(parts) >= 2:
                        body = parts[1].strip()
                        if body and len(body) > 50:
                            return body
                    # Fallback: skip metadata header lines
                    lines = text.split('\n')
                    body_start = 0
                    for i, line in enumerate(lines):
                        if line.strip() == '---' and i > 3:
                            body_start = i + 1
                            break
                    if body_start:
                        return '\n'.join(lines[body_start:]).strip()
    
    # 2) Fallback to cron output files
    if CRON_OUTPUT_DIR.exists():
        for f in sorted(CRON_OUTPUT_DIR.glob(f'{date_str}*.md')):
            text = f.read_text()
            resp_match = re.search(r'##\s*Response\s*\n', text)
            if not resp_match:
                continue
            after_response = text[resp_match.end():].strip()
            lines = after_response.split('\n')
            content_lines = []
            started = False
            for line in lines:
                stripped = line.strip()
                if not started:
                    if stripped in ('---', '以下是正文：', '以下是本期推文全文：', 
                                   '以下是本期推文的最终定稿：'):
                        started = True
                        continue
                    if re.match(r'^(所有|写作|本期信息|选题)', stripped):
                        continue
                    if re.match(r'^#+\s+', stripped):
                        started = True
                if started:
                    content_lines.append(line)
            if content_lines:
                return '\n'.join(content_lines).strip()
    
    return None


def _build_description(episode, full_content):
    """Build the description field with metadata header + full article."""
    header = (
        f"> *WeChat科普推文 第{episode['number']}期 · {episode['date']}*\n"
        f"> 话题: {episode['topics']}\n\n"
    )
    if full_content:
        return header + full_content
    else:
        return header + f"## {episode['title']}\n\n*(文章正文未找到，请手动补充)*"


def parse_episodes():
    """Parse episodes_tracker.md and return list of episode dicts."""
    if not TRACKER_PATH.exists():
        return []
    
    text = TRACKER_PATH.read_text()
    episodes = []
    
    # Pattern: ## 第N期 | YYYY-MM-DD
    pattern = re.compile(
        r'##\s*第(\d+)期\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\n'
        r'\*\*标题\*\*:\s*(.+?)\s*\n'
        r'\*\*核心话题\*\*:\s*(.+?)\s*\n',
        re.MULTILINE
    )
    
    for match in pattern.finditer(text):
        episodes.append({
            'number': int(match.group(1)),
            'date': match.group(2),
            'title': match.group(3).strip(),
            'topics': match.group(4).strip(),
        })
    
    return episodes


def match_model(episode, config):
    """Match an episode to a model config entry or concept topic."""
    topics_lower = episode['topics'].lower()
    title_lower = episode['title'].lower()
    combined = f"{topics_lower} {title_lower}"
    
    # Try exact model match first
    for model_key, model_cfg in config.get('models', {}).items():
        for kw in model_cfg.get('keywords', []):
            if kw.lower() in combined:
                return 'model', model_key, model_cfg
    
    # Try concept topic match
    for concept_key, concept_cfg in config.get('concept_topics', {}).items():
        if concept_key.lower() in combined:
            return 'concept', concept_key, concept_cfg
    
    return 'unknown', None, None


def generate_cover_image(model_name, model_type, episode_title, width=800, height=400):
    """Generate a unique cover image for each article using PIL."""
    palette = PALETTES.get(model_type, PALETTES['other'])
    img = Image.new('RGB', (width, height), palette[0])
    draw = ImageDraw.Draw(img)
    
    # Gradient background
    for y in range(height):
        t = y / height
        r = int(palette[0][0] + (palette[1][0] - palette[0][0]) * t)
        g = int(palette[0][1] + (palette[1][1] - palette[0][1]) * t)
        b = int(palette[0][2] + (palette[1][2] - palette[0][2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Abstract cell structures
    random.seed(hash(model_name) % 2**32)
    for _ in range(15):
        cx = random.randint(50, width - 50)
        cy = random.randint(50, height - 50)
        r = random.randint(15, 50)
        alpha_val = random.randint(20, 60)
        color = palette[random.randint(0, 3)]
        
        for i in range(3):
            rr = r - i * 5
            if rr > 0:
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                odraw = ImageDraw.Draw(overlay)
                odraw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                              outline=color + (alpha_val // (i + 1),), width=1)
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                draw = ImageDraw.Draw(img)
    
    # Network connections
    draw = ImageDraw.Draw(img)
    random.seed(hash(model_name + "net") % 2**32)
    for _ in range(30):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = x1 + random.randint(-150, 150), y1 + random.randint(-100, 100)
        alpha_val = random.randint(10, 30)
        color = palette[random.randint(0, 3)]
        draw.line([(x1, y1), (x2, y2)], fill=color + (alpha_val,), width=1)
    
    # Glowing nodes
    for _ in range(20):
        x, y = random.randint(30, width - 30), random.randint(30, height - 30)
        r = random.randint(2, 4)
        glow_r = r * 3
        for gr in range(glow_r, r, -1):
            alpha_val = max(0, 30 - gr * 4)
            draw.ellipse([x - gr, y - gr, x + gr, y + gr],
                         fill=(220, 230, 255, alpha_val))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(240, 245, 255))
    
    # Dark semi-transparent overlay for text readability
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 60))
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    
    # Save to bytes
    buffer = BytesIO()
    img.convert('RGB').save(buffer, 'JPEG', quality=90)
    buffer.seek(0)
    return buffer


def get_or_create_tag(name):
    tag, _ = Tag.objects.get_or_create(name=name)
    return tag


class Command(BaseCommand):
    help = 'Sync WeChat article episodes to ModelEntry records'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        parser.add_argument('--episode', type=int, help='Sync a specific episode number')
        parser.add_argument('--force', action='store_true', help='Re-sync even already-synced episodes')
        parser.add_argument('--backfill', action='store_true', help='Update existing entries with full article content')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_episode = options.get('episode')
        force = options['force']
        backfill = options['backfill']
        
        config = load_config()
        episodes = parse_episodes()
        sync_log = load_sync_log()
        
        if not episodes:
            self.stdout.write(self.style.WARNING('No episodes found in tracker.'))
            return
        
        if target_episode:
            episodes = [e for e in episodes if e['number'] == target_episode]
            if not episodes:
                self.stdout.write(self.style.ERROR(f'Episode {target_episode} not found.'))
                return
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for ep in episodes:
            ep_id = str(ep['number'])
            
            # Skip already synced (unless --force or --backfill)
            if ep_id in sync_log.get('synced_episodes', []) and not force and not backfill:
                self.stdout.write(f"  ⏭  Episode {ep_id} already synced — skip")
                skipped_count += 1
                continue
            
            # Extract full article content
            full_content = extract_article_content(ep)
            if full_content:
                self.stdout.write(f"  📄 Ep{ep_id}: article found ({len(full_content)} chars)")
            else:
                self.stdout.write(self.style.WARNING(f"  ⚠️  Ep{ep_id}: no article content found"))
            
            match_type, match_key, match_cfg = match_model(ep, config)
            
            if match_type == 'model':
                # Try to find existing model entry
                existing = ModelEntry.objects.filter(
                    name__iexact=match_cfg['name']
                ).first()
                
                if existing:
                    # Update wechat fields + backfill full article content
                    existing.wechat_article_title = ep['title']
                    if full_content:
                        existing.description = _build_description(ep, full_content)
                    if not dry_run:
                        existing.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ Ep{ep_id} → updated existing: {existing.name}")
                    )
                else:
                    # Create new model entry
                    if dry_run:
                        self.stdout.write(f"  📝 Ep{ep_id} → would create: {match_cfg['name']}")
                        created_count += 1
                    else:
                        entry = self._create_entry(ep, match_cfg)
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  🆕 Ep{ep_id} → created: {entry.name}")
                        )
            
            elif match_type == 'concept':
                # Create concept article entry
                name = f"{match_cfg.get('name_prefix', 'Article')}: {ep['title']}"
                
                existing = ModelEntry.objects.filter(name=name).first()
                if existing:
                    existing.wechat_article_title = ep['title']
                    if full_content:
                        existing.description = _build_description(ep, full_content)
                    if not dry_run:
                        existing.save()
                    updated_count += 1
                    self.stdout.write(f"  ✅ Ep{ep_id} → updated concept: {name}")
                else:
                    if dry_run:
                        self.stdout.write(f"  📝 Ep{ep_id} → would create concept: {name}")
                        created_count += 1
                    else:
                        concept_cfg = {
                            'name': name,
                            'model_type': match_cfg.get('model_type', 'other'),
                            'modality': match_cfg.get('modality', 'scrna'),
                            'short_description': match_cfg.get('short_description', ''),
                            'paper_title': '',
                            'paper_url': '',
                            'github_url': '',
                            'authors': '',
                            'journal': '',
                        }
                        entry = self._create_entry(ep, concept_cfg)
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  🆕 Ep{ep_id} → created concept: {entry.name}")
                        )
            else:
                # Unknown topic — create generic entry
                name = ep['title']
                if dry_run:
                    self.stdout.write(f"  📝 Ep{ep_id} → would create generic: {name}")
                    created_count += 1
                else:
                    generic_cfg = {
                        'name': name,
                        'model_type': 'other',
                        'modality': 'scrna',
                        'short_description': ep['topics'],
                        'paper_title': '',
                        'paper_url': '',
                        'github_url': '',
                        'authors': '',
                        'journal': '',
                    }
                    entry = self._create_entry(ep, generic_cfg)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  🆕 Ep{ep_id} → created generic: {entry.name}")
                    )
            
            # Mark as synced (only if not backfilling — backfill just updates content)
            if not dry_run and not backfill:
                sync_log.setdefault('synced_episodes', []).append(ep_id)
        
        if not dry_run:
            sync_log['last_sync'] = datetime.now().isoformat()
            save_sync_log(sync_log)
        
        # Summary
        self.stdout.write('')
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: {created_count} would create, {updated_count} would update, '
                    f'{skipped_count} skipped.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Done: {created_count} created, {updated_count} updated, {skipped_count} skipped.'
                )
            )

    def _create_entry(self, episode, cfg):
        """Create a ModelEntry from episode data and config."""
        full_content = extract_article_content(episode)
        description = _build_description(episode, full_content)
        
        entry = ModelEntry(
            name=cfg['name'],
            short_description=cfg.get('short_description', episode['topics']),
            description=description,
            paper_title=cfg.get('paper_title', ''),
            paper_url=cfg.get('paper_url', ''),
            github_url=cfg.get('github_url', ''),
            website_url=cfg.get('website_url', ''),
            huggingface_url=cfg.get('huggingface_url', ''),
            wechat_article_title=episode['title'],
            authors=cfg.get('authors', ''),
            journal=cfg.get('journal', ''),
            model_type=cfg.get('model_type', 'other'),
            modality=cfg.get('modality', 'scrna'),
            architecture=cfg.get('architecture', ''),
            parameter_count=cfg.get('parameter_count', ''),
            pretraining_data=cfg.get('pretraining_data', ''),
            publication_date=episode['date'],
            featured=False,
            published=True,
        )
        entry.save()
        
        # Generate and attach cover image
        cover_buffer = generate_cover_image(
            cfg['name'], cfg.get('model_type', 'other'), episode['title']
        )
        slug = slugify(cfg['name'])[:50]
        entry.cover_image.save(
            f'{slug}_cover.jpg',
            ContentFile(cover_buffer.read()),
            save=True
        )
        
        # Add "WeChat" tag
        tag = get_or_create_tag('WeChat')
        entry.tags.add(tag)
        
        return entry
