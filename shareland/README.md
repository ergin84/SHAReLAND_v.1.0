# SHAReLAND Project

<div align="center">
  <img src="shreland_homepage.png" alt="SHAReLAND Homepage Screenshot" width="600"/>
  <br/>
  <b>Figure 1: SHAReLAND Homepage</b>
  <br/><br/>
  <img src="shareland_catalog.png" alt="SHAReLAND Catalog Screenshot" width="600"/>
  <br/>
  <b>Figure 2: SHAReLAND Catalog View</b>
</div>

SHAReLAND is a Django-based web platform designed for the collection, documentation, and visualization of archaeological data. It supports the collaborative management of research projects, archaeological sites, and evidences, offering a structured and multilingual interface for scientific data entry and spatial referencing.

## Features

* User authentication and profile management
* Project-based research creation with detailed metadata
* Management of archaeological sites:

  * Georeferenced using coordinates or polygon shapefiles
  * Linked to investigation data, bibliographies, and sources
* Management of archaeological evidences:

  * Descriptive, spatial, and contextual data
  * Linked to both research and sites
* Interactive 2D map visualization (Leaflet)
* Import of shapefiles and direct drawing of geometries on map
* AJAX-based dynamic form inputs for region/province/municipality

## Technologies

* **Backend**: Django 5.2, Python 3.12, PostgreSQL with PostGIS
* **Frontend**: HTML5, Bootstrap 5, Leaflet.js, JavaScript
* **GIS Tools**: Shapefile upload, WKT geometry fields, centroid calculation

## Project Structure

```
├── django_project/
│   ├── frontend/           # Main application (models, views, forms, templates)
│   ├── users/              # User registration and profiles
│   ├── templates/          # Shared and app-specific templates
│   ├── static/             # CSS, JS, media
│   ├── media/              # Uploaded files and shapefiles
│   └── manage.py           # Django CLI
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the repo**:

   ```bash
   git clone https://github.com/ergin84/ShareLand.git
   cd shareland
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL/PostGIS**:

   * Ensure a PostgreSQL database with PostGIS extension is created
   * Update `settings.py` with your DB credentials

5. **Run migrations**:

   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**:

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:

   ```bash
   python manage.py runserver
   ```

## Deployment

### Docker Deployment

1. Prepare your `.env` file (see `deployment.env.example`).
2. Deploy with:
   ```bash
   ./deployment.sh
   ```
   This will sync your code, copy the environment, and restart the Docker stack on your VPS.

### Non-Docker Deployment (Direct VPS)

1. Prepare your `.env` file (see `deployment.env.example`).
2. Deploy with:
   ```bash
   ./deployment_nodocker.sh /path/to/.env
   ```
   This will:
   - Sync code and environment
   - Install all dependencies (Python, Nginx, Certbot, Supervisor, PostgreSQL)
   - Set up Gunicorn and Nginx with SSL (Let's Encrypt)
   - Schedule nightly DB backups to Google Drive (requires `gdrive` CLI and `GDRIVE_FOLDER_ID`)
   - Set up health checks and auto-restart

## Database Backup

- Nightly at 2am, the database is backed up and uploaded to Google Drive.
- Configure `GDRIVE_FOLDER_ID` in your `.env`.

## Environment File

- Use `deployment.env.example` as a template for your `.env`.
- All deployment, DB, mail, and backup settings are loaded from this file.

## Contribution Guidelines

* Fork the repository and create feature branches
* Follow Django best practices and PEP8 style
* Open pull requests for review and merge

## License

This project is released under the MIT License.

## Contact

For more information, contact the development team at: [ergin.mehmeti@logos-ri.eu](mailto:ergin.mehmti@logos-ri.eu)
