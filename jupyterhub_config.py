# JupyterHub configuration for webapp-starter

# Basic JupyterHub configuration
c.JupyterHub.ip = '0.0.0.0'
c.JupyterHub.port = 8000
c.JupyterHub.hub_ip = '0.0.0.0'

# Database configuration - use dedicated jupyterhub database
c.JupyterHub.db_url = 'postgresql://postgres:postgres@postgres:5432/jupyterhub'

# Docker spawner configuration
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'

# Docker spawner settings - use custom image with pre-installed dependencies
c.DockerSpawner.image = 'webapp-starter-jupyter:latest'
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

# Environment variables for Jupyter
c.DockerSpawner.environment = {
    'JUPYTER_ENABLE_LAB': 'yes',
    'SHELL': '/bin/bash'
}

# Use default command from custom image (dependencies already installed)
# c.DockerSpawner.cmd is not needed since the image has the right defaults

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

# Use dummy authenticator with fixed password for development
c.JupyterHub.authenticator_class = 'jupyterhub.auth.DummyAuthenticator'

# Simple password for all users in development
c.DummyAuthenticator.password = 'admin'

# Allow any user to access (create users automatically)
c.Authenticator.allow_all = True

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