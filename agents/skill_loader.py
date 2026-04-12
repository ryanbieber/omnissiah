"""
SkillLoader: Load SKILL.md files with YAML frontmatter and modular skill structure

Supports skillsdirectory.com-compliant skill format:
- SKILL.md: Main skill file with YAML frontmatter and markdown content
- references/: Detailed reference documentation
- scripts/: Executable scripts (Python, shell, etc.)
- templates/: Reusable file templates with {{VARIABLE}} markers
- assets/: Static resources (configs, images, JSON data)

Progressive loading:
- Metadata always loaded (name, version, tools, etc.)
- Content loaded when accessed
- References/templates on-demand
"""

import logging
import json
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """YAML frontmatter metadata for skills."""
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = "Unknown"
    keywords: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    region: Optional[str] = None
    zone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Skill:
    """Complete skill with metadata, content, and resources."""
    metadata: SkillMetadata
    content: str = ""
    references: Dict[str, str] = field(default_factory=dict)
    scripts: Dict[str, Path] = field(default_factory=dict)
    templates: Dict[str, str] = field(default_factory=dict)
    assets: Dict[str, Path] = field(default_factory=dict)
    
    def get_reference(self, name: str) -> Optional[str]:
        """Get reference content by name."""
        return self.references.get(name)
    
    def get_script_path(self, name: str) -> Optional[Path]:
        """Get script path by name."""
        return self.scripts.get(name)
    
    def get_template(self, name: str) -> Optional[str]:
        """Get template content by name."""
        return self.templates.get(name)
    
    def get_asset(self, name: str) -> Optional[Path]:
        """Get asset path by name."""
        return self.assets.get(name)


class SkillLoader:
    """Load and manage skills from SKILL.md files."""
    
    def __init__(self, skills_root: str = None):
        """Initialize skill loader.
        
        Args:
            skills_root: Root directory containing skill categories
                        Defaults to agents/skills/
        """
        if skills_root is None:
            skills_root = str(Path(__file__).parent / "skills")
        
        self.skills_root = Path(skills_root)
        self.skill_index: Dict[str, Skill] = {}
        self.categories: Dict[str, List[Skill]] = {}
        self.category_index: Dict[str, str] = {}
        
        logger.info(f"SkillLoader initialized with root: {self.skills_root}")
    
    def load_all_skills(self) -> Dict[str, List[Skill]]:
        """Load all skills from root directory.
        
        Structure:
        skills_root/
        ├── car_maintenance/
        │   ├── SKILL.md
        │   ├── references/
        │   ├── scripts/
        │   ├── templates/
        │   └── assets/
        ├── house_maintenance/
        └── lawncare/
        
        Returns:
            Dictionary mapping category_name -> list of Skill objects
        """
        if not self.skills_root.exists():
            logger.error(f"Skills root not found: {self.skills_root}")
            return {}
        
        for category_dir in self.skills_root.iterdir():
            if not category_dir.is_dir():
                continue
            
            category_name = category_dir.name
            skill_file = category_dir / "SKILL.md"
            
            if not skill_file.exists():
                logger.debug(f"⏭️  No SKILL.md in {category_name}")
                continue
            
            try:
                skill = self._load_skill(skill_file, category_name)
                if skill:
                    if category_name not in self.categories:
                        self.categories[category_name] = []
                    
                    self.categories[category_name].append(skill)
                    self.skill_index[skill.metadata.name] = skill
                    self.category_index[skill.metadata.name] = category_name
                    
                    logger.info(f"✅ Loaded {skill.metadata.name} from {category_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load {category_name}: {e}")
        
        return self.categories
    
    def _load_skill(self, skill_file: Path, category_name: str) -> Optional[Skill]:
        """Load a single SKILL.md file with all resources.
        
        Args:
            skill_file: Path to SKILL.md
            category_name: Name of the category (e.g., 'lawncare')
        
        Returns:
            Skill object or None if loading failed
        """
        try:
            with open(skill_file, 'r') as f:
                content = f.read()
            
            # Parse YAML frontmatter and markdown content
            metadata, body = self._parse_frontmatter(content)
            
            # Load all resources from subdirectories
            category_dir = skill_file.parent
            references = self._load_references(category_dir / "references")
            scripts = self._load_scripts(category_dir / "scripts")
            templates = self._load_templates(category_dir / "templates")
            assets = self._load_assets(category_dir / "assets")
            
            # Create Skill object
            skill = Skill(
                metadata=metadata,
                content=body,
                references=references,
                scripts=scripts,
                templates=templates,
                assets=assets
            )
            
            return skill
        
        except Exception as e:
            logger.error(f"Failed to load skill from {skill_file}: {e}")
            return None
    
    def _parse_frontmatter(self, content: str) -> tuple[SkillMetadata, str]:
        """Parse YAML frontmatter from SKILL.md.
        
        Format:
        ---
        name: skill_name
        description: Description
        tools: [tool1, tool2]
        ---
        # Markdown content here
        
        Args:
            content: Full file content
        
        Returns:
            Tuple of (SkillMetadata, markdown_body)
        """
        try:
            lines = content.split('\n', 1)
            
            # Check if frontmatter exists
            if not lines[0].strip().startswith('---'):
                return SkillMetadata(name="unknown", description=""), content
            
            # Split frontmatter and body
            parts = content.split('---', 2)
            if len(parts) < 3:
                return SkillMetadata(name="unknown", description=""), content
            
            frontmatter_str = parts[1]
            body = parts[2].strip()
            
            # Parse YAML
            frontmatter = yaml.safe_load(frontmatter_str) or {}
            
            # Create metadata
            metadata = SkillMetadata(
                name=frontmatter.get("name", "unknown"),
                description=frontmatter.get("description", ""),
                version=frontmatter.get("version", "1.0.0"),
                author=frontmatter.get("author", "Unknown"),
                keywords=frontmatter.get("keywords", []),
                tools=frontmatter.get("tools", []),
                region=frontmatter.get("region"),
                zone=frontmatter.get("zone"),
                created_at=frontmatter.get("created_at"),
                updated_at=frontmatter.get("updated_at"),
                tags=frontmatter.get("tags", [])
            )
            
            return metadata, body
        
        except Exception as e:
            logger.warning(f"Failed to parse frontmatter: {e}")
            return SkillMetadata(name="unknown", description=""), content
    
    def _load_references(self, ref_dir: Path) -> Dict[str, str]:
        """Load reference files from references/ directory.
        
        Args:
            ref_dir: Path to references directory
        
        Returns:
            Dictionary mapping filename (without extension) -> content
        """
        references = {}
        if not ref_dir.exists():
            return references
        
        for ref_file in ref_dir.glob("*.md"):
            try:
                with open(ref_file, 'r') as f:
                    references[ref_file.stem] = f.read()
            except Exception as e:
                logger.warning(f"Failed to load reference {ref_file}: {e}")
        
        return references
    
    def _load_scripts(self, script_dir: Path) -> Dict[str, Path]:
        """Load script files from scripts/ directory.
        
        Args:
            script_dir: Path to scripts directory
        
        Returns:
            Dictionary mapping script name -> Path to script file
        """
        scripts = {}
        if not script_dir.exists():
            return scripts
        
        for script_file in script_dir.glob("*"):
            if script_file.is_file() and script_file.suffix in ['.py', '.sh', '.js']:
                scripts[script_file.stem] = script_file
        
        return scripts
    
    def _load_templates(self, template_dir: Path) -> Dict[str, str]:
        """Load template files from templates/ directory.
        
        Args:
            template_dir: Path to templates directory
        
        Returns:
            Dictionary mapping template name -> template content
        """
        templates = {}
        if not template_dir.exists():
            return templates
        
        for template_file in template_dir.glob("*.template"):
            try:
                with open(template_file, 'r') as f:
                    templates[template_file.stem] = f.read()
            except Exception as e:
                logger.warning(f"Failed to load template {template_file}: {e}")
        
        return templates
    
    def _load_assets(self, asset_dir: Path) -> Dict[str, Path]:
        """Load asset files from assets/ directory.
        
        Args:
            asset_dir: Path to assets directory
        
        Returns:
            Dictionary mapping asset name -> Path to asset file
        """
        assets = {}
        if not asset_dir.exists():
            return assets
        
        for asset_file in asset_dir.iterdir():
            if asset_file.is_file():
                assets[asset_file.name] = asset_file
        
        return assets
    
    # Public API Methods
    
    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name.
        
        Args:
            skill_name: Name of skill (from YAML metadata)
        
        Returns:
            Skill object or None
        """
        return self.skill_index.get(skill_name)
    
    def get_category_skills(self, category_name: str) -> List[Skill]:
        """Get all skills for a category.
        
        Args:
            category_name: Name of category (e.g., 'lawncare')
        
        Returns:
            List of Skill objects
        """
        return self.categories.get(category_name, [])
    
    def list_skills(self) -> List[str]:
        """List all skill names.
        
        Returns:
            List of skill names
        """
        return list(self.skill_index.keys())
    
    def list_categories(self) -> List[str]:
        """List all skill categories.
        
        Returns:
            List of category names
        """
        return list(self.categories.keys())
    
    def get_all_categories_summary(self) -> Dict[str, Dict]:
        """Get summary of all categories and skills.
        
        Returns:
            Dictionary with structure:
            {
                'category_name': {
                    'count': int,
                    'skills': [skill_names],
                    'tools': [tool_names]
                }
            }
        """
        summary = {}
        for cat_name, skills in self.categories.items():
            summary[cat_name] = {
                'count': len(skills),
                'skills': [s.metadata.name for s in skills],
                'tools': self._collect_tools(skills)
            }
        return summary
    
    def _collect_tools(self, skills: List[Skill]) -> List[str]:
        """Collect all tool names from skills.
        
        Args:
            skills: List of Skill objects
        
        Returns:
            Sorted list of unique tool names
        """
        tools = set()
        for skill in skills:
            tools.update(skill.metadata.tools or [])
        return sorted(list(tools))
    
    def get_skill_content_for_llm(self, skill_name: str) -> str:
        """Get skill content formatted for LLM context.
        
        Args:
            skill_name: Name of skill
        
        Returns:
            Formatted markdown content
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return ""
        
        content = f"# {skill.metadata.name}\n\n"
        content += f"{skill.metadata.description}\n\n"
        content += skill.content
        
        if skill.metadata.tools:
            content += f"\n\nAvailable Tools: {', '.join(skill.metadata.tools)}"
        
        return content
    
    def export_to_json(self, output_file: str = None) -> str:
        """Export skill index to JSON.
        
        Args:
            output_file: Path to save JSON (defaults to skills_index.json in root)
        
        Returns:
            Path to exported JSON file
        """
        if output_file is None:
            output_file = str(self.skills_root / "skills_index.json")
        
        export_data = {}
        for category, skills in self.categories.items():
            export_data[category] = {
                'count': len(skills),
                'skills': [
                    {
                        'name': s.metadata.name,
                        'description': s.metadata.description,
                        'version': s.metadata.version,
                        'tools': s.metadata.tools,
                        'scripts': list(s.scripts.keys()) if s.scripts else [],
                        'templates': list(s.templates.keys()) if s.templates else [],
                        'references': list(s.references.keys()) if s.references else [],
                        'tags': s.metadata.tags,
                        'region': s.metadata.region,
                        'zone': s.metadata.zone
                    }
                    for s in skills
                ]
            }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"✅ Exported skills to {output_file}")
        return output_file
    
    def get_formatted_descriptions(self) -> str:
        """Get formatted skill descriptions for system prompt.
        
        Returns:
            Markdown formatted descriptions of all skills and tools
        """
        descriptions = []
        descriptions.append("# Available Skills & Tools\n")
        
        for cat_name, skills in self.categories.items():
            descriptions.append(f"\n## {cat_name.replace('_', ' ').title()}\n")
            
            for skill in skills:
                descriptions.append(f"### {skill.metadata.name}")
                descriptions.append(skill.metadata.description)
                
                if skill.metadata.tools:
                    descriptions.append(f"\n**Tools:** {', '.join(skill.metadata.tools)}")
                
                if skill.metadata.region:
                    descriptions.append(f"**Region:** {skill.metadata.region}")
                
                descriptions.append("")
        
        return "\n".join(descriptions)


# Singleton instance
_skill_loader: Optional[SkillLoader] = None


def get_skill_loader(skills_root: str = None) -> SkillLoader:
    """Get or create skill loader singleton.
    
    Args:
        skills_root: Root path to skills folder
    
    Returns:
        SkillLoader instance
    """
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader(skills_root)
        _skill_loader.load_all_skills()
    return _skill_loader


def reload_skills(skills_root: str = None) -> SkillLoader:
    """Force reload of skills from disk.
    
    Args:
        skills_root: Root path to skills folder
    
    Returns:
        New SkillLoader instance
    """
    global _skill_loader
    _skill_loader = SkillLoader(skills_root)
    _skill_loader.load_all_skills()
    return _skill_loader


if __name__ == "__main__":
    """CLI entry point for testing skill ingestion"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    print("\n🔄 Loading skills from agents/skills/ ...\n")
    loader = get_skill_loader()
    
    print("=" * 60)
    print("SKILL CATEGORIES")
    print("=" * 60)
    
    summary = loader.get_all_categories_summary()
    total_skills = 0
    
    for cat_name, cat_info in summary.items():
        display_name = cat_name.replace('_', ' ').upper()
        print(f"\n📁 {display_name}")
        print(f"   Skills: {cat_info['count']}")
        print(f"   Tools: {', '.join(cat_info['tools']) if cat_info['tools'] else 'None'}")
        total_skills += cat_info['count']
        
        for skill in cat_info['skills']:
            print(f"      ✓ {skill}")
    
    print("\n" + "=" * 60)
    print(f"✅ Total categories: {len(summary)}")
    print(f"✅ Total skills: {total_skills}")
    print("=" * 60 + "\n")
    
    # Export to JSON
    json_file = loader.export_to_json()
    print(f"📤 Exported to: {json_file}\n")
