# Project Elara - AI Life Coach Application

## Project Overview
Elara is a personalized life coach web application that integrates goal-setting, daily planning, and self-reflection based on proven psychological principles. Currently designed as a single-user application for personal use.

## Core Psychological Foundations

### 1. Human-Computer Interaction (HCI)
- **Fitts's Law**: Important actions are easily accessible
- **Hick's Law**: Limited choices to reduce decision fatigue
- **Miller's Law**: Maximum 7±2 items in working memory (dashboard shows max 5)
- **Immediate feedback**: Every action has visual/audio response

### 2. Self-Determination Theory (SDT)
- **Autonomy**: User defines own goals and values, chooses avatar personality
- **Competence**: Progress bars, achievement system, skill progression
- **Relatedness**: Avatar as supportive companion with memory of past interactions

### 3. Cognitive Behavioral Therapy (CBT)
- **Thought Records**: Structured templates for cognitive restructuring
- **ABC Model**: Tracking Activating events → Beliefs → Consequences
- **Behavioral Activation**: Scheduling pleasant activities
- **Cognitive Distortions**: Identifying patterns (all-or-nothing, catastrophizing, etc.)

### 4. Habit Loop
- **Cue**: Time-based or context-based triggers
- **Routine**: The tracked behavior
- **Reward**: Points, badges, avatar reactions, streak counters
- **Craving**: Building anticipation through preview of rewards

## Key Features

### 1. Avatar System
Five personality types user can choose from:
- **The Sage** 🧙‍♂️ - Wise, philosophical, asks deep questions
- **The Champion** 🏆 - Energetic cheerleader, celebrates wins  
- **The Friend** 🤝 - Warm, empathetic, non-judgmental
- **The Strategist** 🎯 - Analytical, data-driven, practical
- **The Zen Master** 🧘 - Calm, mindful, focuses on present

### 2. Wheel of Life
Eight life dimensions for self-assessment:
- Career, Health, Relationships, Finance, Fun, Growth, Family, Spirituality
- Monthly tracking with visual spider chart
- Identifies areas needing attention

### 3. Calendar & Task Management
- Monthly/weekly/daily views
- Task-goal hierarchy
- Energy level indicators (high/medium/low)
- Integration with habit tracking

## Technical Stack

### Core Technologies
- **Backend**: Flask (Python)
- **Database**: SQLite (dev) / PostgreSQL (prod) with SQLAlchemy ORM + Flask-Migrate
- **Frontend**: HTML templates with Bootstrap
- **Authentication**: Flask-Login (single user)
- **AI Integration**: DeepSeek API (cost-effective alternative to Gemini)
- **Deployment**: Render
- **Dependency Management**: pip-tools (pip-compile & pip-sync)
- **Version Control**: GitHub

### Project Structure
```
elara/
├── app.py                 # Main Flask application
├── models.py              # SQLAlchemy models
├── routes/                # Route blueprints
│   ├── auth.py           # Authentication routes
│   ├── dashboard.py      # Main dashboard
│   ├── journal.py        # Journaling & CBT features
│   ├── habits.py         # Habit tracking
│   ├── goals.py          # Goals & tasks
│   ├── wheel.py          # Wheel of Life
│   └── avatar.py         # AI coach interface
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── dashboard.html    # Main dashboard
│   ├── journal.html      # Journal entry
│   ├── calendar.html     # Calendar view
│   └── wheel.html        # Wheel of Life
├── static/               
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript
│   └── img/              # Images & avatars
├── services/             
│   ├── cbt_analyzer.py   # CBT pattern detection
│   ├── habit_tracker.py  # Habit loop logic
│   ├── ai_coach.py       # DeepSeek integration
│   └── insights.py       # Pattern analysis
├── database.db           # SQLite database
├── requirements.in       # pip-tools source
├── requirements.txt      # Compiled dependencies
├── config.py            # Configuration settings
└── README.md            # User documentation
```

## Database Schema

### Core Tables
```python
User(id, username, password_hash, avatar_personality, created_at)
Value(id, user_id, name, description, priority)
Goal(id, user_id, title, value_id, target_date, status, progress)
Task(id, user_id, goal_id, title, completed, due_date, energy_required)
```

### CBT Tables
```python
JournalEntry(id, user_id, content, mood_score, energy_level, created_at)
ThoughtRecord(id, user_id, situation, automatic_thought, emotion, 
              intensity, evidence_for, evidence_against, balanced_thought)
CognitiveDistortion(id, name, description)  # Pre-populated
UserDistortion(id, user_id, distortion_id, journal_entry_id)
```

### Habit Tables
```python
Habit(id, user_id, name, cue_type, cue_time, routine, reward, active)
HabitLog(id, habit_id, completed_at, streak_count)
```

### Assessment Tables
```python
LifeAssessment(id, user_id, career, health, relationships, 
               finance, fun, growth, family, spirituality, timestamp)
```

### AI/Avatar Tables
```python
ChatMessage(id, user_id, content, sender, personality_response, timestamp)
Insight(id, user_id, pattern_type, description, data_points, created_at)
Achievement(id, name, description, criteria, icon)  # Pre-populated
UserAchievement(id, user_id, achievement_id, unlocked_at)
```

### System Tables
```python
NotificationSchedule(id, user_id, type, frequency, next_trigger)
UserPreference(id, user_id, key, value)
```

## Progressive Disclosure Timeline (User Experience)

### Week 1: Foundation
- Simple login
- Basic journaling with mood tracking
- Avatar introduction (personality selection)

### Week 2: Goals
- Unlock goal setting after 3 journal entries
- Simple task creation
- Daily dashboard activation

### Week 3: Habits  
- Unlock habit tracker after 7-day streak
- First habit with cue-routine-reward setup
- Streak counter activation

### Month 2: Intelligence
- Wheel of Life assessment unlocked
- Weekly review with avatar
- First AI-generated insights

### Month 3: Advanced
- CBT thought records unlocked
- Full pattern analysis
- Context-aware chat with avatar

## Development Priorities

### Phase 1: MVP Foundation
1. Flask project setup with pip-tools
2. SQLAlchemy models creation
3. Basic authentication (single user)
4. Simple journaling with mood tracking
5. Dashboard with HCI principles

### Phase 2: Core Features
1. Goal and task management
2. Habit loop tracker
3. Avatar personality selection
4. Calendar integration
5. Basic progress visualization

### Phase 3: Intelligence Layer
1. DeepSeek API integration
2. Weekly review system
3. Wheel of Life assessment
4. Pattern detection engine
5. Insight generation

### Phase 4: Advanced Features
1. CBT thought record templates
2. Cognitive distortion identification
3. Progressive disclosure system
4. Achievement system
5. Notification scheduler

### Phase 5: Polish & Deploy
1. UI/UX refinement
2. Data export functionality
3. Backup system
4. Deploy to Render
5. Performance optimization

## Key Constraints & Decisions

1. **Single User**: No complex multi-user auth needed initially
2. **SQLite**: Sufficient for single user, easy migration to PostgreSQL later
3. **Flask**: Simpler than Next.js, Python ecosystem familiarity
4. **DeepSeek API**: More cost-effective than Gemini for experimentation
5. **No Overkill**: Avoid Prisma, Clerk, NextAuth - keep it simple
6. **pip-tools**: Use pip-compile and pip-sync for dependency management
7. **Progressive Disclosure**: Features unlock based on engagement, not time

## UI Layout Concept

### Main Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│  ELARA                    [Today] [Calendar] [Goals] [Life]  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ╔═══════════════════════════════════════╗    │
│  │  Avatar  │  ║  Welcome back!                        ║    │
│  │    😊    │  ║  You have 3 tasks today               ║    │
│  │ [Chat]   │  ╚═══════════════════════════════════════╝    │
│  └──────────┘                                                │
│                                                               │
│  TODAY'S FOCUS                          QUICK JOURNAL        │
│  ┌─────────────────────────┐  ┌──────────────────────┐      │
│  │ □ Morning meditation     │  │ How are you feeling? │      │
│  │ ✓ Review project docs    │  │ __________________ │      │
│  │ □ Call with team         │  │ [Save entry]       │      │
│  └─────────────────────────┘  └──────────────────────┘      │
│                                                               │
│  WEEKLY PROGRESS               HABIT STREAK                  │
│  ┌─────────────────────────┐  ┌──────────────────────┐      │
│  │ ████████░░ 80% complete │  │ 🔥 5 days journaling │      │
│  └─────────────────────────┘  └──────────────────────┘      │
└───────────────────────────────────────────────────────────────┘
```

## Future Enhancements (Post-MVP)

1. **Webhook System**: Integration with external calendars, task managers
2. **Mobile App**: React Native or PWA for on-the-go access
3. **Multi-user Support**: When ready to scale beyond personal use
4. **Advanced Analytics**: Machine learning for deeper pattern recognition
5. **Voice Interface**: Audio journaling and voice commands
6. **Export/Import**: Full data portability in JSON/CSV formats

## Development Commands

```bash
# Install dependencies
pip-compile requirements.in
pip-sync requirements.txt

# Run development server
flask run --debug

# Database migrations (using Flask-Migrate)
flask db init                                # Initialize migrations (one-time)
flask db migrate -m "Description"           # Generate new migration
flask db upgrade                            # Apply pending migrations
flask db downgrade                          # Rollback last migration
flask db current                            # Show current revision
flask db history                            # View migration history

# Run tests
pytest

# Deploy to Render
git push origin main  # Render auto-deploys from GitHub
```

## Notes for Future Claude Sessions

- This is a single-user application for personal use
- Prioritize simplicity over scalability initially  
- The user prefers pragmatic solutions over complex architectures
- Progressive disclosure is for USER experience, not development timeline
- All psychological principles must be actively integrated, not just mentioned
- The avatar personality deeply affects the entire user experience
- CBT features are core to the journaling system, not an add-on