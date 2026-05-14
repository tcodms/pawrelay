from ai.anomaly.channels import BACKUP_EXHAUSTED_CHANNEL
from functools import partial

from ai.anomaly.channels import CHECKPOINT_DELAY_CHANNEL
from ai.anomaly.channels import NEEDS_VERIFY_CHANNEL
from ai.anomaly.channels import PING_NO_RESPONSE_CHANNEL
from ai.anomaly.channels import PRE_DEPARTURE_NO_SHOW_CHANNEL
from ai.anomaly.channels import SOS_CHANNEL
from ai.anomaly.handlers import handle_backup_exhausted
from ai.anomaly.handlers import handle_checkpoint_delay
from ai.anomaly.handlers import handle_needs_verify
from ai.anomaly.handlers import handle_ping_no_response
from ai.anomaly.handlers import handle_pre_departure_no_show
from ai.anomaly.handlers import handle_sos


def build_handlers(shelter_path=None):
    return {
        SOS_CHANNEL: partial(handle_sos, shelter_path=shelter_path),
        NEEDS_VERIFY_CHANNEL: partial(handle_needs_verify, shelter_path=shelter_path),
        CHECKPOINT_DELAY_CHANNEL: partial(handle_checkpoint_delay, shelter_path=shelter_path),
        BACKUP_EXHAUSTED_CHANNEL: partial(handle_backup_exhausted, shelter_path=shelter_path),
        PING_NO_RESPONSE_CHANNEL: partial(handle_ping_no_response, shelter_path=shelter_path),
        PRE_DEPARTURE_NO_SHOW_CHANNEL: partial(handle_pre_departure_no_show, shelter_path=shelter_path),
    }


async def decide(channel, payload, shelter_path=None):
    handlers = build_handlers(shelter_path)
    return await handlers[channel](payload)
