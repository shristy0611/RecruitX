"""
Skills taxonomy manager for RecruitPro AI.

This module provides functionality for loading, managing, and utilizing
industry-specific skills taxonomies with hierarchical classification.
"""

import os
import json
import logging
from typing import Dict, List, Set, Optional, Any, Union
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class SkillNode:
    """Node in the skills taxonomy tree."""
    
    def __init__(
        self, 
        name: str,
        category: Optional[str] = None,
        parent: Optional["SkillNode"] = None,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a skill node.
        
        Args:
            name: Name of the skill
            category: Optional category (technical, domain, soft)
            parent: Optional parent node
            aliases: Optional list of alternative names
            metadata: Optional metadata dictionary
        """
        self.name = name
        self.category = category
        self.parent = parent
        self.children = []
        self.aliases = aliases or []
        self.metadata = metadata or {}
    
    def add_child(self, child: "SkillNode") -> None:
        """
        Add a child node to this skill.
        
        Args:
            child: Child node to add
        """
        child.parent = self
        self.children.append(child)
    
    def to_dict(self, include_children: bool = True) -> Dict[str, Any]:
        """
        Convert node to dictionary representation.
        
        Args:
            include_children: Whether to include children nodes
            
        Returns:
            Dictionary representation
        """
        result = {
            "name": self.name,
            "category": self.category,
            "aliases": self.aliases,
            "metadata": self.metadata
        }
        
        if include_children and self.children:
            result["children"] = [child.to_dict() for child in self.children]
            
        return result
    
    def get_ancestors(self) -> List[str]:
        """
        Get list of ancestor skill names.
        
        Returns:
            List of ancestor names from root to parent
        """
        ancestors = []
        node = self.parent
        
        while node:
            ancestors.insert(0, node.name)
            node = node.parent
            
        return ancestors
    
    def get_descendants(self) -> List[str]:
        """
        Get list of descendant skill names.
        
        Returns:
            List of all descendant skill names
        """
        descendants = []
        
        for child in self.children:
            descendants.append(child.name)
            descendants.extend(child.get_descendants())
            
        return descendants
    
    def find_child(self, name: str) -> Optional["SkillNode"]:
        """
        Find a direct child node by name.
        
        Args:
            name: Name of the child to find
            
        Returns:
            SkillNode if found, None otherwise
        """
        name_lower = name.lower()
        
        for child in self.children:
            if child.name.lower() == name_lower:
                return child
                
        return None
    
    def __str__(self) -> str:
        """String representation of the node."""
        return f"{self.name} ({len(self.children)} children)"


class SkillsTaxonomyManager:
    """Manager for loading and utilizing skills taxonomies."""
    
    def __init__(self, taxonomies_dir: Optional[str] = None):
        """
        Initialize the taxonomy manager.
        
        Args:
            taxonomies_dir: Optional directory containing taxonomy files
        """
        self.taxonomies_dir = taxonomies_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "data", "taxonomies"
        )
        
        # Dictionary of loaded taxonomies by domain
        self.taxonomies: Dict[str, SkillNode] = {}
        
        # Flattened skill lookup for quick access
        self._skill_lookup: Dict[str, SkillNode] = {}
        
        # Load default taxonomies if available
        self._load_default_taxonomies()
    
    def load_taxonomy(
        self, 
        domain: str, 
        file_path: Optional[str] = None
    ) -> bool:
        """
        Load a taxonomy from file.
        
        Args:
            domain: Domain identifier for the taxonomy
            file_path: Optional path to taxonomy file, if not using default location
            
        Returns:
            Boolean indicating success
        """
        try:
            # Determine file path if not provided
            if not file_path:
                file_path = os.path.join(self.taxonomies_dir, f"{domain.lower()}_taxonomy.json")
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"Taxonomy file not found: {file_path}")
                return False
            
            # Load taxonomy from file
            with open(file_path, 'r') as f:
                taxonomy_data = json.load(f)
            
            # Build taxonomy tree
            root = self._build_taxonomy_tree(taxonomy_data, domain)
            
            # Store the taxonomy
            self.taxonomies[domain] = root
            
            # Update skill lookup
            self._update_skill_lookup(domain)
            
            logger.info(f"Loaded taxonomy for domain: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading taxonomy for domain {domain}: {e}")
            return False
    
    def save_taxonomy(
        self, 
        domain: str, 
        file_path: Optional[str] = None
    ) -> bool:
        """
        Save a taxonomy to file.
        
        Args:
            domain: Domain identifier for the taxonomy
            file_path: Optional path to save taxonomy file
            
        Returns:
            Boolean indicating success
        """
        try:
            if domain not in self.taxonomies:
                logger.warning(f"No taxonomy loaded for domain: {domain}")
                return False
            
            # Determine file path if not provided
            if not file_path:
                file_path = os.path.join(self.taxonomies_dir, f"{domain.lower()}_taxonomy.json")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert taxonomy to dictionary
            taxonomy_dict = self.taxonomies[domain].to_dict()
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(taxonomy_dict, f, indent=2)
            
            logger.info(f"Saved taxonomy for domain: {domain} to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving taxonomy for domain {domain}: {e}")
            return False
    
    def add_skill(
        self,
        domain: str,
        skill_name: str,
        category: Optional[str] = None,
        parent_path: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a skill to the taxonomy.
        
        Args:
            domain: Domain identifier for the taxonomy
            skill_name: Name of the skill to add
            category: Optional category (technical, domain, soft)
            parent_path: Optional path to parent node
            aliases: Optional list of alternative names
            metadata: Optional metadata dictionary
            
        Returns:
            Boolean indicating success
        """
        try:
            # Check if taxonomy exists
            if domain not in self.taxonomies:
                logger.warning(f"No taxonomy loaded for domain: {domain}")
                return False
            
            # Check if skill already exists
            if self.find_skill(domain, skill_name):
                logger.warning(f"Skill '{skill_name}' already exists in domain {domain}")
                return False
            
            # Create new skill node
            new_skill = SkillNode(
                name=skill_name,
                category=category,
                aliases=aliases,
                metadata=metadata
            )
            
            # Find parent node
            if parent_path:
                parent = self.taxonomies[domain]
                
                # Navigate the path
                for name in parent_path:
                    child = parent.find_child(name)
                    if not child:
                        logger.warning(f"Parent path node '{name}' not found")
                        return False
                    parent = child
                
                # Add to parent
                parent.add_child(new_skill)
            else:
                # Add to root
                self.taxonomies[domain].add_child(new_skill)
            
            # Update skill lookup
            self._skill_lookup[f"{domain}:{skill_name.lower()}"] = new_skill
            
            logger.info(f"Added skill '{skill_name}' to domain {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding skill '{skill_name}' to domain {domain}: {e}")
            return False
    
    def find_skill(
        self, 
        domain: str, 
        skill_name: str
    ) -> Optional[SkillNode]:
        """
        Find a skill by name in the taxonomy.
        
        Args:
            domain: Domain identifier for the taxonomy
            skill_name: Name of the skill to find
            
        Returns:
            SkillNode if found, None otherwise
        """
        # Check if domain exists
        if domain not in self.taxonomies:
            logger.warning(f"No taxonomy loaded for domain: {domain}")
            return None
        
        # Look up skill by name
        lookup_key = f"{domain}:{skill_name.lower()}"
        return self._skill_lookup.get(lookup_key)
    
    def get_skill_hierarchy(
        self, 
        domain: str, 
        skill_name: str
    ) -> Dict[str, Any]:
        """
        Get the hierarchical position of a skill.
        
        Args:
            domain: Domain identifier for the taxonomy
            skill_name: Name of the skill
            
        Returns:
            Dictionary with ancestors and descendants
        """
        skill = self.find_skill(domain, skill_name)
        
        if not skill:
            return {"ancestors": [], "descendants": []}
        
        return {
            "ancestors": skill.get_ancestors(),
            "descendants": skill.get_descendants()
        }
    
    def get_related_skills(
        self, 
        domain: str, 
        skill_name: str,
        max_distance: int = 2
    ) -> List[str]:
        """
        Get related skills based on taxonomy proximity.
        
        Args:
            domain: Domain identifier for the taxonomy
            skill_name: Name of the skill
            max_distance: Maximum hierarchical distance
            
        Returns:
            List of related skill names
        """
        skill = self.find_skill(domain, skill_name)
        
        if not skill:
            return []
        
        related = set()
        
        # Add siblings (skills with same parent)
        if skill.parent:
            for sibling in skill.parent.children:
                if sibling.name != skill_name:
                    related.add(sibling.name)
        
        # Add immediate children
        for child in skill.children:
            related.add(child.name)
        
        # Add parent and grandparent
        ancestor = skill.parent
        distance = 1
        
        while ancestor and distance <= max_distance:
            related.add(ancestor.name)
            ancestor = ancestor.parent
            distance += 1
        
        return list(related)
    
    def export_flat_taxonomy(self, domain: str) -> Dict[str, Dict[str, Any]]:
        """
        Export a flattened version of the taxonomy.
        
        Args:
            domain: Domain identifier for the taxonomy
            
        Returns:
            Dictionary mapping skill names to their properties
        """
        if domain not in self.taxonomies:
            logger.warning(f"No taxonomy loaded for domain: {domain}")
            return {}
        
        result = {}
        
        def process_node(node, path=[]):
            # Create entry for this node
            node_path = path + [node.name]
            result[node.name] = {
                "category": node.category,
                "aliases": node.aliases,
                "path": node_path,
                "has_children": len(node.children) > 0,
                "metadata": node.metadata
            }
            
            # Process children
            for child in node.children:
                process_node(child, node_path)
        
        # Start from root's children (skip the domain root itself)
        for child in self.taxonomies[domain].children:
            process_node(child)
        
        return result
    
    def get_all_domains(self) -> List[str]:
        """
        Get list of all loaded taxonomy domains.
        
        Returns:
            List of domain identifiers
        """
        return list(self.taxonomies.keys())
    
    def create_taxonomy(self, domain: str) -> bool:
        """
        Create a new empty taxonomy.
        
        Args:
            domain: Domain identifier for the new taxonomy
            
        Returns:
            Boolean indicating success
        """
        if domain in self.taxonomies:
            logger.warning(f"Taxonomy already exists for domain: {domain}")
            return False
        
        # Create root node
        root = SkillNode(name=domain, category="domain")
        self.taxonomies[domain] = root
        
        logger.info(f"Created new taxonomy for domain: {domain}")
        return True
    
    def generate_default_taxonomy(self, domain: str) -> bool:
        """
        Generate a default taxonomy for common domains.
        
        Args:
            domain: Domain identifier (e.g., "tech", "healthcare", "finance")
            
        Returns:
            Boolean indicating success
        """
        if domain.lower() == "tech":
            # Create tech taxonomy if not exist
            if not self.create_taxonomy("tech"):
                return False
            
            # Add common tech skills
            programming_languages = [
                "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "PHP", "Swift",
                "Go", "Kotlin", "TypeScript", "Rust", "Scala"
            ]
            
            # Add programming languages category
            self.add_skill("tech", "Programming Languages", "technical")
            
            for lang in programming_languages:
                self.add_skill("tech", lang, "technical", ["Programming Languages"])
            
            # Add frameworks category
            self.add_skill("tech", "Frameworks", "technical")
            
            # Web frameworks
            self.add_skill("tech", "Web Frameworks", "technical", ["Frameworks"])
            web_frameworks = [
                "React", "Angular", "Vue.js", "Django", "Flask", "Express.js", 
                "Spring Boot", "Laravel", "Ruby on Rails"
            ]
            
            for framework in web_frameworks:
                self.add_skill("tech", framework, "technical", ["Frameworks", "Web Frameworks"])
            
            # Data science
            self.add_skill("tech", "Data Science", "technical")
            data_science_skills = [
                "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
                "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy"
            ]
            
            for skill in data_science_skills:
                self.add_skill("tech", skill, "technical", ["Data Science"])
            
            # Save the taxonomy
            self.save_taxonomy("tech")
            return True
            
        elif domain.lower() == "soft_skills":
            # Create soft skills taxonomy
            if not self.create_taxonomy("soft_skills"):
                return False
            
            # Communication skills
            self.add_skill("soft_skills", "Communication", "soft")
            communication_skills = [
                "Public Speaking", "Writing", "Active Listening", "Negotiation",
                "Presentation", "Conflict Resolution"
            ]
            
            for skill in communication_skills:
                self.add_skill("soft_skills", skill, "soft", ["Communication"])
            
            # Leadership skills
            self.add_skill("soft_skills", "Leadership", "soft")
            leadership_skills = [
                "Team Management", "Strategic Planning", "Delegation",
                "Mentoring", "Motivation", "Decision Making"
            ]
            
            for skill in leadership_skills:
                self.add_skill("soft_skills", skill, "soft", ["Leadership"])
            
            # Save the taxonomy
            self.save_taxonomy("soft_skills")
            return True
            
        else:
            logger.warning(f"No default taxonomy available for domain: {domain}")
            return False
    
    def _load_default_taxonomies(self) -> None:
        """Load default taxonomies from the taxonomies directory."""
        # Ensure directory exists
        os.makedirs(self.taxonomies_dir, exist_ok=True)
        
        # Find all taxonomy files
        taxonomy_files = [f for f in os.listdir(self.taxonomies_dir) 
                         if f.endswith("_taxonomy.json")]
        
        for file in taxonomy_files:
            # Extract domain from filename
            domain = file.replace("_taxonomy.json", "")
            
            # Load the taxonomy
            self.load_taxonomy(domain)
        
        # If no taxonomies loaded, create default tech taxonomy
        if not self.taxonomies:
            self.generate_default_taxonomy("tech")
            self.generate_default_taxonomy("soft_skills")
    
    def _build_taxonomy_tree(
        self, 
        data: Dict[str, Any], 
        name: str
    ) -> SkillNode:
        """
        Build a taxonomy tree from dictionary data.
        
        Args:
            data: Dictionary representation of taxonomy
            name: Name for the root node
            
        Returns:
            Root SkillNode of the built tree
        """
        # Create root node
        root = SkillNode(
            name=name,
            category=data.get("category"),
            aliases=data.get("aliases", []),
            metadata=data.get("metadata", {})
        )
        
        # Process children
        for child_data in data.get("children", []):
            child = self._build_taxonomy_tree(child_data, child_data["name"])
            root.add_child(child)
        
        return root
    
    def _update_skill_lookup(self, domain: str) -> None:
        """
        Update the flattened skill lookup for a domain.
        
        Args:
            domain: Domain to update lookup for
        """
        if domain not in self.taxonomies:
            return
        
        # Process all nodes in the domain
        def process_node(node):
            # Add to lookup
            self._skill_lookup[f"{domain}:{node.name.lower()}"] = node
            
            # Process aliases
            for alias in node.aliases:
                self._skill_lookup[f"{domain}:{alias.lower()}"] = node
            
            # Process children
            for child in node.children:
                process_node(child)
        
        # Start processing
        process_node(self.taxonomies[domain])
