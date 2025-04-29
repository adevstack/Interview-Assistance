"""
ASGI config for CloudFlare Workers / ASGI server deployment
"""
import os
from app import create_app

# Create ASGI application
asgi_app = create_app()

# For Cloudflare Workers with Hypercorn
def app(scope):
    return asgi_app(scope)
