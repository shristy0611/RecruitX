import React from 'react';

const SkillList = ({ skills, title, className = '', badgeColor = 'blue' }) => {
  // Handle case where skills might be an object with details property
  if (skills && skills.details && Array.isArray(skills.details)) {
    skills = skills.details;
  }
  
  if (!skills || !Array.isArray(skills) || skills.length === 0) {
    return null;
  }

  // Function to extract the skill text from a skill item, which might be a string or an object
  const getSkillText = (skill) => {
    if (!skill) return '';
    
    if (typeof skill === 'string') {
      return skill;
    }
    
    // If it has a 'skill' property (some API responses use this format)
    if (skill.skill) {
      const level = skill.level || skill.proficiency || skill.importance || '';
      return level ? `${skill.skill} (${level})` : skill.skill;
    }
    
    // If it has a 'name' property (some API responses use this format)
    if (skill.name) {
      const level = skill.level || skill.proficiency || skill.importance || '';
      
      // Handle nested items if they exist
      if (Array.isArray(skill.items)) {
        return level 
          ? `${skill.name}: ${skill.items.join(', ')} (${level})` 
          : `${skill.name}: ${skill.items.join(', ')}`;
      }
      
      // Just name and level
      return level ? `${skill.name} (${level})` : skill.name;
    }
    
    // Fallback - try to convert to string or return a placeholder
    return String(skill) !== '[object Object]' ? String(skill) : 'Unknown skill';
  };

  return (
    <div className={className}>
      {title && <h3 className="text-lg font-semibold mb-2">{title}</h3>}
      <div className="flex flex-wrap gap-2">
        {skills.map((skill, index) => (
          <span key={index} className={`badge badge-${badgeColor}`}>
            {getSkillText(skill)}
          </span>
        ))}
      </div>
    </div>
  );
};

export default SkillList; 