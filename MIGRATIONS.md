# Database Migrations Guide

This document covers how to manage database schema changes using Flask-Migrate in the Elara project.

## Overview

Elara uses Flask-Migrate (which wraps Alembic) to handle database schema versioning and migrations. This allows us to:

- Track schema changes in version control
- Apply updates safely to production
- Rollback changes if needed
- Support both SQLite (development) and PostgreSQL (production)

## Common Commands

### Development Workflow

```bash
# Generate a new migration after model changes
python -m flask db migrate -m "Description of changes"

# Review the generated migration file in migrations/versions/
# Edit if necessary, then apply it locally:
python -m flask db upgrade

# Check current migration status
python -m flask db current

# View migration history
python -m flask db history
```

### Production Deployment

Migrations run automatically during Render deployments via `build.sh`:
```bash
python -m flask db upgrade
```

### Rollback Commands

```bash
# Rollback one migration
python -m flask db downgrade

# Rollback to specific revision
python -m flask db downgrade <revision_id>
```

## Making Model Changes

1. **Edit models** in `models/__init__.py`
2. **Generate migration**: `python -m flask db migrate -m "descriptive message"`
3. **Review generated file** in `migrations/versions/` - check for accuracy
4. **Test locally**: `python -m flask db upgrade`
5. **Commit migration file** to git
6. **Deploy** - migrations run automatically on Render

## Migration File Structure

```
migrations/
├── alembic.ini          # Alembic configuration
├── env.py               # Migration environment setup
├── README               # Alembic's README
├── script.py.mako       # Migration template
└── versions/            # Individual migration files
    └── bbe80a3f3d7f_add_onboarding_columns.py
```

## Best Practices

### Before Creating Migration

- **Backup production data** (Render handles this automatically)
- **Test model changes thoroughly** in development
- **Consider impact** on existing data

### Migration Code Review

- **Check column types** match your models
- **Verify default values** are appropriate
- **Test both upgrade() and downgrade()** functions
- **Consider data migration** for complex changes

### Production Safety

- **Always review** generated migrations before deploying
- **Test migrations** on development database first
- **Monitor deployments** for any migration errors
- **Have rollback plan** ready

## Troubleshooting

### "No changes in schema detected"

This happens when:
- Local database already matches models
- Running migration on wrong database
- Models haven't been imported properly

**Solution**: Use `flask db revision -m "message"` to create empty migration, then edit manually.

### Migration conflicts

If multiple developers create migrations simultaneously:
```bash
# Merge migrations if needed
python -m flask db merge <revision1> <revision2>
```

### Production migration failures

1. **Check Render logs** for specific error
2. **Verify environment variables** are set correctly
3. **Ensure DATABASE_URL** points to correct PostgreSQL instance
4. **Rollback if necessary**: redeploy previous version

### Reset migrations (development only)

```bash
# Remove migrations folder
rm -rf migrations/

# Reinitialize
python -m flask db init
python -m flask db migrate -m "Initial migration"
```

## Environment-Specific Notes

### Development (SQLite)
- Migrations stored in `data/elara.db`
- Full reset possible by deleting database file
- Faster iteration during development

### Production (PostgreSQL on Render)
- Migrations applied automatically on deploy
- Database managed by Render
- Backups handled by Render

## Migration History

| Migration | Date | Description |
|-----------|------|-------------|
| bbe80a3f3d7f | 2025-09-14 | Add onboarding_completed, onboarding_step, is_pro_mode columns to users table |

## Emergency Procedures

### Production Database Issue

1. **Check Render dashboard** for service status
2. **Review deployment logs** for migration errors
3. **If migration failed**: redeploy previous working version
4. **If data corruption**: contact Render support for backup restore

### Local Development Issues

1. **Reset local database**: delete `data/elara.db`
2. **Reinitialize migrations**: follow reset process above
3. **Sync with production schema** if needed

## Support

- **Render Documentation**: https://render.com/docs/databases
- **Flask-Migrate Documentation**: https://flask-migrate.readthedocs.io/
- **Alembic Documentation**: https://alembic.sqlalchemy.org/