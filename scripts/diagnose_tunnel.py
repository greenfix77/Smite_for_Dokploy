#!/usr/bin/env python3
"""Diagnostic script to check tunnel configuration"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, '/app')

from app.database import AsyncSessionLocal
from app.models import Tunnel
from sqlalchemy import select


async def check_tunnels():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tunnel).where(Tunnel.status == "active"))
        tunnels = result.scalars().all()
        
        if not tunnels:
            print("No active tunnels found")
            return
        
        for t in tunnels:
            print(f"\nTunnel: {t.name} ({t.id})")
            print(f"  Core: {t.core}, Type: {t.type}")
            print(f"  remote_port: {t.spec.get('remote_port', 'NOT SET')}")
            print(f"  listen_port: {t.spec.get('listen_port', 'NOT SET')}")
            print(f"  forward_to: {t.spec.get('forward_to', 'NOT SET')}")
            print(f"  Full spec: {t.spec}")


if __name__ == "__main__":
    asyncio.run(check_tunnels())

