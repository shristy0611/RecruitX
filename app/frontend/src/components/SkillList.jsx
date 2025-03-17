import React from 'react';

const SkillList = ({ skills, title, className = '', badgeColor = 'blue' }) => {
  // Handle case where skills might be an object with details property
  if (skills && skills.details && Array.isArray(skills.details)) {
    skills = skills.details;
  }
  
  if (!skills || !Array.isArray(skills) || skills.length === 0) {
    return (
      <div className={className}>
        {title && <h3 className="text-lg font-semibold mb-2 text-high-contrast">{title}</h3>}
        <p className="text-medium-contrast italic text-sm">No items found</p>
      </div>
    );
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
      {title && <h3 className="text-lg font-semibold mb-2 text-high-contrast">{title}</h3>}
      <div className="flex flex-wrap gap-2">
        {skills.map((skill, index) => {
          const badgeClasses = {
            blue: "bg-blue-100 text-blue-800 dark:bg-blue-700 dark:text-blue-50",
            green: "bg-green-100 text-green-800 dark:bg-green-700 dark:text-green-50",
            yellow: "bg-yellow-100 text-yellow-800 dark:bg-yellow-700 dark:text-yellow-50",
            red: "bg-red-100 text-red-800 dark:bg-red-700 dark:text-red-50",
            purple: "bg-purple-100 text-purple-800 dark:bg-purple-700 dark:text-purple-50"
          };
          
          return (
            <span 
              key={index} 
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeClasses[badgeColor] || badgeClasses['blue']}`}
            >
              {getSkillText(skill)}
            </span>
          );
        })}
      </div>
    </div>
  );
};

export default SkillList; 