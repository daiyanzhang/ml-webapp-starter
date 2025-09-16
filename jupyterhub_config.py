# JupyterHub configuration for webapp-starter

# Basic JupyterHub configuration
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000
c.JupyterHub.hub_ip = '0.0.0.0'

# Database configuration - use dedicated jupyterhub database
c.JupyterHub.db_url = 'postgresql://postgres:postgres@postgres:5432/jupyterhub'

# Docker spawner configuration
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

# Docker spawner settings
c.DockerSpawner.image = 'jupyter/minimal-notebook:latest'
c.DockerSpawner.remove = False
c.DockerSpawner.network_name = 'webapp-starter_default'

# Hub connection settings for spawned containers
c.JupyterHub.hub_connect_ip = 'jupyterhub'

# Volume mounts - unified directory with user subdirectories
c.DockerSpawner.volumes = {
    '/Users/DaiyanZhang/xpeng-project/webapp-starter/notebooks': '/home/jovyan/work',  # 使用相对路径
}

# User-specific notebook directory
c.DockerSpawner.notebook_dir = '/home/jovyan/work/users/{username}'

# Simplified resource limits
c.DockerSpawner.extra_host_config = {
    'mem_limit': '2g'
}

# Set environment variable to auto-install utils package
c.DockerSpawner.environment = {
    'JUPYTER_ENABLE_LAB': 'yes',
    'SETUP_UTILS_PACKAGE': 'true'
}

# Custom startup command to install utils package and requirements
c.DockerSpawner.cmd = ['bash', '-c', '''
if [ "$SETUP_UTILS_PACKAGE" = "true" ]; then
    cd /home/jovyan/work && pip install -r requirements.txt 2>/dev/null || echo "Warning: Failed to install requirements.txt"
    cd /home/jovyan/work && pip install -e . 2>/dev/null || echo "Warning: Failed to install utils package"
fi
exec start-notebook.sh --NotebookApp.token="" --NotebookApp.password=""
''']

# Hub service configuration
c.JupyterHub.services = [
    {
        'name': 'webapp-starter-api',
        'url': 'http://backend:8000',
        'api_token': 'webapp-starter-hub-api-token',
        'admin': True  # Give admin privileges to the service
    }
]

# API token for external services with admin privileges
c.JupyterHub.api_tokens = {
    'webapp-starter-hub-api-token': 'webapp-starter-api'
}

# Use null authenticator for development (no authentication required)
c.JupyterHub.authenticator_class = 'jupyterhub.auth.NullAuthenticator'

# Admin users
c.Authenticator.admin_users = {'admin', 'webapp-starter-api'}

# User options
c.Spawner.default_url = '/lab'  # Start with JupyterLab

# Timeout settings
c.Spawner.start_timeout = 300
c.Spawner.http_timeout = 120

# Logging
c.JupyterHub.log_level = 'DEBUG'
c.DockerSpawner.debug = True

# Shutdown settings
c.JupyterHub.shutdown_on_logout = True