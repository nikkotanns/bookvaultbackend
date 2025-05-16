from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from aiobotocore.config import AioConfig
from aioboto3 import Session
from app.config import settings

config = AioConfig(
    request_checksum_calculation='WHEN_REQUIRED',
    response_checksum_validation='WHEN_REQUIRED'
)

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

def get_s3_client():
    session = Session()
    return session.client(
        "s3",
        endpoint_url=settings.endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.region,
        config=config,
    )
