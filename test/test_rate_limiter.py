import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, Request
from ratelimiter import rate_limit


@pytest.fixture
def mock_redis():
    with patch("ratelimiter.r", autospec=True) as mock_redis:
        mock_redis.zremrangebyscore = AsyncMock()
        mock_redis.zcard = AsyncMock()
        mock_redis.zadd = AsyncMock()
        mock_redis.expire = AsyncMock()
        yield mock_redis


@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    return request


@pytest.mark.asyncio
async def test_rate_limit_anonymous_under_limit(mock_redis, mock_request):
    mock_redis.zcard.return_value = 1

    await rate_limit(mock_request, user_id=None)

    mock_redis.zremrangebyscore.assert_called_once()
    mock_redis.zcard.assert_called_once()
    mock_redis.zadd.assert_called_once()
    mock_redis.expire.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_anonymous_at_limit(mock_redis, mock_request):
    mock_redis.zcard.return_value = 2
    with pytest.raises(HTTPException) as exc_info:
        await rate_limit(mock_request, user_id=None)

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many requests for rate limit"

    mock_redis.zremrangebyscore.assert_called_once()
    mock_redis.zcard.assert_called_once()
    mock_redis.zadd.assert_not_called()
    mock_redis.expire.assert_not_called()


@pytest.mark.asyncio
async def test_rate_limit_authenticated_under_limit(mock_redis, mock_request):
    mock_redis.zcard.return_value = 5
    user_id = "1"
    await rate_limit(mock_request, user_id=user_id)

    key = f"rate_limit_{user_id}"
    mock_redis.zremrangebyscore.assert_called_once()
    mock_redis.zcard.assert_called_once()
    mock_redis.zadd.assert_called_once()
    mock_redis.expire.assert_called_once_with(key, 60)


@pytest.mark.asyncio
async def test_rate_limit_authenticated_at_limit(mock_redis, mock_request):
    mock_redis.zcard.return_value = 10
    user_id = "1"

    with pytest.raises(HTTPException) as exc_info:
        await rate_limit(mock_request, user_id=user_id)

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many requests for rate limit"

    mock_redis.zremrangebyscore.assert_called_once()
    mock_redis.zcard.assert_called_once()
    mock_redis.zadd.assert_not_called()
    mock_redis.expire.assert_not_called()
