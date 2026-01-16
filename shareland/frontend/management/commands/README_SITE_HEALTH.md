# SHAReLAND Site Health Check

This management command checks basic site health (database connection, disk space) and notifies admins via email if issues are found.

## Usage

Run the following command from your Django project root:

```
python manage.py site_health_check
```

- If all checks pass, you will see a success message.
- If any check fails, admins (as defined in `settings.ADMINS`) will receive an email alert.

## Checks Performed
- **Database connection**: Ensures all configured databases are reachable.
- **Disk space**: Warns if less than 1GB is free on the root filesystem.

## Scheduling
To run this check automatically, add it to your server's cron jobs or a scheduled task runner.

Example (daily at 2am):
```
0 2 * * * /path/to/venv/bin/python /path/to/manage.py site_health_check
```

## Configuration
- Admin emails are set in your `.env` and `settings.py` (`ADMIN_EMAIL`).
- Ensure your email backend is configured for outgoing mail.
