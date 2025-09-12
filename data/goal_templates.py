"""
Goal Templates Library
Pre-built SMART goal templates for each life area (2-3 per area)
"""

GOAL_TEMPLATES = [
    # Career & Work (3 templates)
    {
        'life_area': 'Career & Work',
        'title': 'Improve Work-Life Balance',
        'description': 'Set clear boundaries between work and personal time to reduce stress and increase satisfaction in both areas.',
        'suggested_tasks': [
            'Define specific work hours and communicate them to colleagues',
            'Create an end-of-day shutdown ritual',
            'Block out personal time in calendar as "busy"',
            'Turn off work notifications after hours'
        ],
        'difficulty': 'medium',
        'time_estimate': '30 days'
    },
    {
        'life_area': 'Career & Work',
        'title': 'Develop a New Professional Skill',
        'description': 'Learn and apply a new skill relevant to your career growth within the next 3 months.',
        'suggested_tasks': [
            'Research and choose a skill aligned with career goals',
            'Find learning resources (course, book, mentor)',
            'Dedicate 30 minutes daily to practice',
            'Apply the skill in a real project'
        ],
        'difficulty': 'hard',
        'time_estimate': '3 months'
    },
    {
        'life_area': 'Career & Work',
        'title': 'Expand Professional Network',
        'description': 'Build meaningful connections in your industry by networking consistently.',
        'suggested_tasks': [
            'Attend one industry event per month',
            'Connect with 2 new professionals weekly on LinkedIn',
            'Schedule coffee chats with colleagues',
            'Join a professional association or group'
        ],
        'difficulty': 'medium',
        'time_estimate': '2 months'
    },
    
    # Health & Fitness (3 templates)
    {
        'life_area': 'Health & Fitness',
        'title': 'Establish Daily Exercise Routine',
        'description': 'Build a sustainable exercise habit by starting with 30 minutes of movement daily.',
        'suggested_tasks': [
            'Choose activities you enjoy (walking, yoga, dancing)',
            'Schedule exercise at the same time each day',
            'Track progress with a fitness app or journal',
            'Find an accountability partner'
        ],
        'difficulty': 'medium',
        'time_estimate': '30 days'
    },
    {
        'life_area': 'Health & Fitness',
        'title': 'Improve Sleep Quality',
        'description': 'Develop better sleep habits to get 7-8 hours of quality rest each night.',
        'suggested_tasks': [
            'Set consistent bedtime and wake time',
            'Create a calming bedtime routine',
            'Remove screens from bedroom',
            'Track sleep patterns for 2 weeks'
        ],
        'difficulty': 'easy',
        'time_estimate': '21 days'
    },
    {
        'life_area': 'Health & Fitness',
        'title': 'Adopt Healthier Eating Habits',
        'description': 'Make sustainable changes to your diet for better energy and health.',
        'suggested_tasks': [
            'Meal prep healthy lunches on Sundays',
            'Add one serving of vegetables to each meal',
            'Replace sugary drinks with water',
            'Keep a food journal for awareness'
        ],
        'difficulty': 'medium',
        'time_estimate': '30 days'
    },
    
    # Relationships (3 templates)
    {
        'life_area': 'Relationships',
        'title': 'Strengthen Family Bonds',
        'description': 'Dedicate quality time to nurture relationships with family members.',
        'suggested_tasks': [
            'Schedule weekly family dinner or activity',
            'Call distant relatives monthly',
            'Plan a family outing or trip',
            'Create new family traditions'
        ],
        'difficulty': 'easy',
        'time_estimate': '2 months'
    },
    {
        'life_area': 'Relationships',
        'title': 'Deepen Friendships',
        'description': 'Invest in meaningful friendships through regular connection and support.',
        'suggested_tasks': [
            'Reach out to one friend weekly',
            'Plan monthly friend gatherings',
            'Remember and celebrate important dates',
            'Practice active listening in conversations'
        ],
        'difficulty': 'easy',
        'time_estimate': '30 days'
    },
    {
        'life_area': 'Relationships',
        'title': 'Improve Communication Skills',
        'description': 'Enhance your ability to connect and communicate effectively with others.',
        'suggested_tasks': [
            'Practice "I" statements in conflicts',
            'Ask more open-ended questions',
            'Give full attention during conversations',
            'Express gratitude daily to someone'
        ],
        'difficulty': 'medium',
        'time_estimate': '6 weeks'
    },
    
    # Money & Finance (2 templates)
    {
        'life_area': 'Money & Finance',
        'title': 'Build Emergency Fund',
        'description': 'Create financial security by saving 3 months of expenses.',
        'suggested_tasks': [
            'Calculate monthly essential expenses',
            'Set up automatic savings transfer',
            'Cut one unnecessary expense',
            'Track savings progress weekly'
        ],
        'difficulty': 'hard',
        'time_estimate': '6 months'
    },
    {
        'life_area': 'Money & Finance',
        'title': 'Create and Follow Budget',
        'description': 'Take control of finances by tracking income and expenses systematically.',
        'suggested_tasks': [
            'List all income sources and expenses',
            'Choose a budgeting app or spreadsheet',
            'Review spending weekly',
            'Identify areas to reduce spending'
        ],
        'difficulty': 'medium',
        'time_estimate': '30 days'
    },
    
    # Personal Growth (2 templates)
    {
        'life_area': 'Personal Growth',
        'title': 'Develop Daily Learning Habit',
        'description': 'Commit to continuous learning by dedicating time daily to personal development.',
        'suggested_tasks': [
            'Read for 30 minutes before bed',
            'Listen to educational podcasts during commute',
            'Take one online course this quarter',
            'Join a book club or study group'
        ],
        'difficulty': 'easy',
        'time_estimate': '30 days'
    },
    {
        'life_area': 'Personal Growth',
        'title': 'Build Confidence and Self-Esteem',
        'description': 'Develop greater self-confidence through intentional practices and challenges.',
        'suggested_tasks': [
            'List 3 daily wins or accomplishments',
            'Challenge one fear each week',
            'Practice positive self-talk',
            'Celebrate small victories'
        ],
        'difficulty': 'medium',
        'time_estimate': '2 months'
    },
    
    # Fun & Recreation (2 templates)
    {
        'life_area': 'Fun & Recreation',
        'title': 'Rediscover Hobbies and Joy',
        'description': 'Make time for activities that bring you joy and relaxation.',
        'suggested_tasks': [
            'List activities that made you happy as a child',
            'Try one new hobby this month',
            'Schedule "play time" weekly',
            'Join a club or group for your interests'
        ],
        'difficulty': 'easy',
        'time_estimate': '30 days'
    },
    {
        'life_area': 'Fun & Recreation',
        'title': 'Plan Regular Adventures',
        'description': 'Add excitement to life by planning regular adventures, big or small.',
        'suggested_tasks': [
            'Explore a new place monthly',
            'Create a bucket list of experiences',
            'Say yes to spontaneous invitations',
            'Plan a quarterly mini-adventure'
        ],
        'difficulty': 'medium',
        'time_estimate': '3 months'
    },
    
    # Home Environment (2 templates)
    {
        'life_area': 'Home Environment',
        'title': 'Declutter and Organize Living Space',
        'description': 'Create a peaceful, organized home environment that supports your wellbeing.',
        'suggested_tasks': [
            'Declutter one room per week',
            'Donate items not used in past year',
            'Implement organization systems',
            'Maintain daily 10-minute tidy routine'
        ],
        'difficulty': 'medium',
        'time_estimate': '30 days'
    },
    {
        'life_area': 'Home Environment',
        'title': 'Create a Calming Home Sanctuary',
        'description': 'Transform your living space into a restorative environment.',
        'suggested_tasks': [
            'Designate a relaxation corner',
            'Add plants or natural elements',
            'Improve lighting in main areas',
            'Reduce digital clutter and distractions'
        ],
        'difficulty': 'easy',
        'time_estimate': '2 weeks'
    },
    
    # Purpose & Meaning (2 templates)
    {
        'life_area': 'Purpose & Meaning',
        'title': 'Clarify Life Purpose and Values',
        'description': 'Discover what truly matters to you and align your life accordingly.',
        'suggested_tasks': [
            'Complete values assessment exercise',
            'Write a personal mission statement',
            'Journal about meaningful experiences',
            'Identify activities that energize you'
        ],
        'difficulty': 'medium',
        'time_estimate': '30 days'
    },
    {
        'life_area': 'Purpose & Meaning',
        'title': 'Contribute to Something Greater',
        'description': 'Find fulfillment by making a positive impact in your community.',
        'suggested_tasks': [
            'Research causes you care about',
            'Volunteer 2 hours monthly',
            'Share your skills with others',
            'Join a community service group'
        ],
        'difficulty': 'easy',
        'time_estimate': '2 months'
    }
]


def get_templates_for_area(life_area):
    """Get all templates for a specific life area."""
    return [t for t in GOAL_TEMPLATES if t['life_area'] == life_area]


def get_template_by_id(template_id):
    """Get a specific template by its index/id."""
    if 0 <= template_id < len(GOAL_TEMPLATES):
        return GOAL_TEMPLATES[template_id]
    return None


def get_all_life_areas():
    """Get list of all unique life areas."""
    return list(set(t['life_area'] for t in GOAL_TEMPLATES))