#!/bin/bash
echo "=== Tunnel Configuration Diagnostic ==="
echo ""

echo "1. Checking tunnel spec in database:"
docker exec smite-panel python -c "
import asyncio
from app.database import AsyncSessionLocal
from app.models import Tunnel
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tunnel).where(Tunnel.status == 'active'))
        tunnels = result.scalars().all()
        for t in tunnels:
            print(f\"Tunnel: {t.name} ({t.id})\")
            print(f\"  remote_port: {t.spec.get('remote_port', 'NOT SET')}\")
            print(f\"  listen_port: {t.spec.get('listen_port', 'NOT SET')}\")
            print(f\"  forward_to: {t.spec.get('forward_to', 'NOT SET')}\")
            print(f\"  Full spec: {t.spec}\")
            print()

asyncio.run(check())
"

echo ""
echo "2. Checking Xray config on node:"
docker exec smite-node cat /etc/smite-node/xray/*.json 2>/dev/null | python3 -m json.tool || echo "No Xray configs found"

echo ""
echo "3. Testing connectivity:"
echo "   Panel -> Node (10000):"
docker exec smite-panel timeout 2 bash -c 'cat < /dev/null > /dev/tcp/65.109.197.226/10000' 2>&1 && echo "   ✅ OK" || echo "   ❌ FAILED"

echo "   Node -> 3x-ui (9999):"
docker exec smite-node timeout 2 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/9999' 2>&1 && echo "   ✅ OK" || echo "   ❌ FAILED"

echo ""
echo "=== End Diagnostic ==="

