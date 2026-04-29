# Celery Worker Setup Guide

## Overview

SELPH uses Celery for async task processing:
- **Draft Generation**: LangGraph-based response generation
- **Message Processing**: Incoming message handling from channels
- **Voice Synthesis**: Voice cloning (Phase 6)
- **Avatar Generation**: Avatar synthesis (Phase 7)

## Task Queues

| Queue | Purpose | Phase |
|-------|---------|-------|
| `celery` | Default queue for system tasks | 0 |
| `draft_generation` | Draft response generation | 0 |
| `message_processing` | Incoming message processing | 0 |
| `voice_synthesis` | Voice cloning (ElevenLabs/Azure) | 6 |
| `avatar_generation` | Avatar synthesis (RunwayML/D-ID) | 7 |

## Running Locally

### Option 1: Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, Redis, FastAPI, Celery, Flower)
docker-compose up

# In another terminal, test the worker
docker exec selph-celery-worker celery -A app.celery_app inspect active

# View Flower dashboard
# Open http://localhost:5555 in your browser
```

### Option 2: Manual Development Setup

**Prerequisites**:
- PostgreSQL 16 running locally
- Redis running locally
- FastAPI backend running

**Terminal 1 - Backend**:
```bash
cd src/backend
export DATABASE_URL=postgresql://selph:password@localhost:5432/selph
export CELERY_BROKER_URL=redis://localhost:6379/1
export CELERY_RESULT_BACKEND=redis://localhost:6379/2
uvicorn app.main:app --reload
```

**Terminal 2 - Celery Worker**:
```bash
cd src/backend
export DATABASE_URL=postgresql://selph:password@localhost:5432/selph
export CELERY_BROKER_URL=redis://localhost:6379/1
export CELERY_RESULT_BACKEND=redis://localhost:6379/2
celery -A app.celery_app worker --loglevel=info --queues=celery,draft_generation,message_processing
```

**Terminal 3 - Flower Dashboard**:
```bash
cd src/backend
export CELERY_BROKER_URL=redis://localhost:6379/1
export CELERY_RESULT_BACKEND=redis://localhost:6379/2
celery -A app.celery_app flower
```

Then open http://localhost:5555

## Task Examples

### 1. Process Incoming Message

```python
from app.tasks.message_processing import process_incoming_message

# Queue the task
result = process_incoming_message.delay(
    user_id="user-123",
    channel="instagram_dm",
    sender_id="ig-456",
    sender_name="John Doe",
    content="Hey, how are you?",
    channel_metadata={"message_id": "ig-msg-789"}
)

# Get result (blocking)
status = result.get(timeout=10)  # {"status": "success", "message_id": "..."}
```

### 2. Generate Draft Manually

```python
from app.tasks.draft_generation import generate_draft_for_message

# Queue the task
result = generate_draft_for_message.delay(
    message_id="msg-123",
    user_id="user-456"
)

# Check status
print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # Task result when complete
```

### 3. Batch Process Messages

```python
from app.tasks.message_processing import batch_process_messages

messages = [
    {
        "sender_id": "ig-1",
        "sender_name": "Alice",
        "content": "Hello!",
        "metadata": {}
    },
    {
        "sender_id": "ig-2",
        "sender_name": "Bob",
        "content": "Hi there!",
        "metadata": {}
    }
]

result = batch_process_messages.delay(
    user_id="user-123",
    channel="instagram_dm",
    messages=messages
)

print(result.result)  # {"status": "success", "messages_queued": 2, "task_ids": [...]}
```

## Monitoring

### Via Flower Web Dashboard

Access http://localhost:5555 to see:
- **Active Tasks**: Currently running tasks
- **Completed Tasks**: Historical task results
- **Task Graph**: Task dependencies and timing
- **Worker Info**: Worker status, pool size, processed tasks
- **Task Stats**: Task success/failure rates

### Via CLI

```bash
# List active tasks
celery -A app.celery_app inspect active

# Get worker stats
celery -A app.celery_app inspect stats

# Check registered tasks
celery -A app.celery_app inspect registered

# Get task statistics
celery -A app.celery_app events

# Purge all tasks (USE WITH CAUTION)
celery -A app.celery_app purge
```

## Configuration

Edit `src/backend/app/config.py`:

```python
# Celery
celery_broker_url: str = "redis://localhost:6379/1"
celery_result_backend: str = "redis://localhost:6379/2"
celery_task_time_limit: int = 300  # 5 minutes
celery_task_soft_time_limit: int = 250  # 4+ minutes
```

## Troubleshooting

### Worker Not Processing Tasks

```bash
# Check if broker is accessible
redis-cli ping  # Should return PONG

# Check if worker connected to broker
celery -A app.celery_app inspect active_queues

# Check worker logs
celery -A app.celery_app inspect active
```

### Tasks Stuck in Queue

```bash
# Purge queue
celery -A app.celery_app purge

# Revoke all tasks
celery -A app.celery_app control revoke '*'
```

### Database Connection Issues

Ensure DATABASE_URL is set and database is running:
```bash
psql postgresql://selph:password@localhost:5432/selph
```

### Redis Connection Issues

Ensure Redis is running on correct port:
```bash
redis-cli ping  # Should return PONG
redis-cli -a redis_dev_password ping  # If password protected
```

## Phase 0 Implementation

**Current Status**: ✅ Complete

- ✅ Celery app configuration
- ✅ Message processing task
- ✅ Draft generation task (placeholder engine)
- ✅ Voice synthesis task (Phase 6 stub)
- ✅ Avatar generation task (Phase 7 stub)
- ✅ Docker Compose setup with worker + flower
- ✅ Task queues configured

## Next Steps

**Phase 1**: Implement full LangGraph twin engine in draft_generation.py
**Phase 6**: Integrate ElevenLabs for voice synthesis
**Phase 7**: Integrate RunwayML/D-ID for avatar generation

## References

- [Celery Documentation](https://docs.celeryproject.io/)
- [Flower Monitoring](https://flower.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)
