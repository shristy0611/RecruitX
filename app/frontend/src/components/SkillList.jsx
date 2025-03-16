import React from 'react';

const SkillList = ({ skills, title, className = '', badgeColor = 'blue' }) => {
  if (!skills || skills.length === 0) {
    return null;
  }

  // Function to extract the skill text from a skill item, which might be a string or an object
  const getSkillText = (skill) => {
    if (typeof skill === 'string') {
      return skill;
    }
    
    // If it has a 'skill' property (some API responses use this format)
    if (skill.skill) {
      return skill.proficiency ? `${skill.skill} (${skill.proficiency})` : skill.skill;
    }
    
    // If it has a 'name' property (some API responses use this format)
    if (skill.name) {
      // Handle nested items if they exist
      if (Array.isArray(skill.items)) {
        return skill.proficiency 
          ? `${skill.name}: ${skill.items.join(', ')} (${skill.proficiency})` 
          : `${skill.name}: ${skill.items.join(', ')}`;
      }
      
      // Just name and proficiency
      return skill.proficiency ? `${skill.name} (${skill.proficiency})` : skill.name;
    }
    
    // If it has an 'importance' property (for job skills)
    if (skill.importance) {
      return `${skill.skill || skill.name} (${skill.importance})`;
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