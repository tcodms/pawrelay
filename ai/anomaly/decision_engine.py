from functools import partial

from ai.anomaly.channels import CHECKPOINT_DELAY_CHANNEL
from ai.anomaly.channels import NEEDS_VERIFY_CHANNEL
from ai.anomaly.channels import SOS_CHANNEL
from ai.anomaly.handlers import handle_checkpoint_delay
from ai.anomaly.handlers import handle_needs_verify
from ai.anomaly.handlers import handle_sos


def build_handlers(shelter_path=None):
    return {
        SOS_CHANNEL: partial(handle_sos, shelter_path=shelter_path),
        NEEDS_VERIFY_CHANNEL: partial(handle_needs_verify, shelter_path=shelter_path),
        CHECKPOINT_DELAY_CHANNEL: partial(handle_checkpoint_delay, shelter_path=shelter_path),
    }


async def decide(channel, payload, shelter_path=None):
    handlers = build_handlers(shelter_path)
    return await handlers[channel](payload)
