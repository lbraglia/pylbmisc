import argparse
import asyncio
import telegram  # pip install --user python-telegram-bot
from pathlib import Path
from ..tg import bot_token, user_id, group_id


async def main(what, to):
    # handling text or attachment
    what_path = Path(what).resolve()
    send = "file" if what_path.exists() else "msg"
    if send == "file":
        ext = what_path.suffix.lower()
    else:
        msg = what
        
    winston_token = bot_token("winston_lb_bot")
    winston = telegram.Bot(winston_token)
    async with winston:
        if send == "msg":
            await winston.send_message(chat_id = to, text = msg)
        elif ext in {".mp3", ".m4a"}:
            await winston.send_audio(chat_id = to, audio = what_path)
        elif ext in {".png", ".jpg", ".jpeg"}:
            await winston.send_photo(chat_id = to, photo = what_path)
        elif ext in {".mp4"}:
            await winston.send_video(chat_id = to, video = what_path)
        else:
            await winston.send_document(chat_id = to, document = what_path)

        
def winston_sends():
    """
    winston_sends "ciao" user::lucailgarb
    winston_sends file.pdf user::lucailgarb
    winston_sends file.png group::da_salvare
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("what")
    parser.add_argument("to")
    args = parser.parse_args()
    what = args.what
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
    asyncio.run(main(what, to_id))

