# pip install --user python-telegram-bot

import argparse
import asyncio
import telegram
from pathlib import Path
from ..tg import bot_token, user_id, group_id


async def main(path, to):
    winston_token = bot_token("winston_lb_bot")
    winston = telegram.Bot(winston_token)
    async with winston:
        await winston.send_document(chat_id = to, document = path)

        
def winston_sends():
    """
    winston_sends file user::lucailgarb
    winston_sends file group::da_salvare
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("to")
    args = parser.parse_args()
    file = Path(args.file).resolve()
    to = args.to
    to_spl = to.split("::")
    to_type = to_spl[0]
    to_label = to_spl[1]
    if to_type == 'user':
        to_id = user_id(to_label)
    elif to_type == 'group':
        to_id = group_id(to_label)
    else:
        raise ValueError("Currently only user::* and group::* parsed.")
    asyncio.run(main(file, to_id))

