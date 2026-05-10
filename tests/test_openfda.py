import pytest

from app.clients.openfda import OpenFDAClient


@pytest.mark.asyncio
async def test_openfda_lookup():
    client = OpenFDAClient()
    try:
        labels = await client.lookup("dapagliflozin")
        assert len(labels) > 0
        print(f"\nDrug: {labels[0].brand_name} / {labels[0].generic_name}")
        print(f"Indications: {labels[0].indications[:200]}")
    finally:
        await client.close()
