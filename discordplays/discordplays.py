import json
import queue
import threading
import os
from discord.ext import commands
from dotenv import load_dotenv
import pydirectinput as pydi

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CONTROLS = json.loads(os.getenv('CONTROL_DICTIONARY'))
MODERATOR = os.getenv('MODERATOR_ROLE')
QUEUE = queue.Queue(maxsize=100)
WORKER = None


class DiscordBot(commands.Bot):
    listening = False

    def __init__(self):
        super().__init__(command_prefix='!')

        # commands
        @self.command()
        async def ping(ctx):
            """
            Pings bot
            """
            response = "Ready to go!"
            await ctx.send(response, delete_after=10)

        @self.command(name="sd")
        @commands.check_any(commands.has_permissions(administrator=True), commands.has_role(MODERATOR))
        async def shut_down(ctx):
            """
            Shuts down bot
            """
            response = "Shutting down..."
            await ctx.send(response)

            # shut down
            await self.close()

        @self.command()
        @commands.check_any(commands.has_permissions(administrator=True), commands.has_role(MODERATOR))
        # @command.has_role()
        async def accept(ctx):
            """
            Starts bot listening for control messages
            """
            self.listening = True

        @self.command()
        @commands.check_any(commands.has_permissions(administrator=True), commands.has_role(MODERATOR))
        async def reject(ctx):
            """
            Stops bot from listening for control messages
            """
            self.listening = False

    # on join
    async def on_ready(self):
        print(f'{self.user} connected to Discord')

    # on message
    async def on_message(self, message):
        """
        When a user sends a message, the bot checks if it is one of the controls in the control dictionary
        If it is, the bot puts that message in the queue
        """
        if self.listening:
            if CONTROLS.get(message.content.lower()):
                QUEUE.put(message.content.lower())
                ensure_worker()
        await self.process_commands(message)


def ensure_worker():
    """
    Ensures that there is a worker thread when one is needed
    """
    global WORKER

    if WORKER:
        return
    WORKER = threading.Thread(target=consumer, daemon=True, args=(QUEUE,))
    WORKER.start()


def consumer(q):
    """
    Worker thread that uses the message in the queue to make key inputs
    Thread closes if there is nothing in the queue for 60 seconds
    """
    global WORKER

    while True:
        try:
            a = q.get(timeout=60)
            process(a)
            q.task_done()
        except queue.Empty:
            WORKER = None
            break


def process(key):
    """
    Prints key pressed to standard output
    Presses key
    """
    print(key)
    pydi.press(CONTROLS.get(key))


def main():
    bot = DiscordBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
