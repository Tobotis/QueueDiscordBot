# QueueDiscordBot

**Invite the bot:**

https://discord.com/oauth2/authorize?client_id=859795533047922718&scope=bot&permissions=17827840 

**or you want to host it yourself?:**
  - Add your bot token in the ENV-Variable "queuebottoken"
  - Run the mode of your choice

**MODE 1 (attempt_2) needs less permissions:**
-
**USAGE:**
- **Commands**
  - `!helpQ` displays this paragraph
  - `!initQ [name of channel]` pick a channel to be the queue
  - `!endQ` ends the queue
  - `!togglerandom` toggle randomizer mode
  - `!toggleembeds` toggle embeds (display of the current queue)
  - `!togglemessages` toggle messages from the bot
- **Move the bot from queue to main channel to move the next person from queue**    

**MODE 2 (attempt_1):**
-
**USAGE:**
- **Commands**
    - **Commands in all channels**
        - `!helpQ` displays this paragraph
        - `!startQ [name of queue]` hosts a new queue
    - **Commands in manager channel**
        - `!endQ` ends the queue and deletes everything
        - `!next` disconnects the current guest and moves in the next one of the queue
        - `!random` disconnects the current guest and moves in a random guest from the queue
        - `!kick` disconnects the current guest

- **Reactions**
    - `⏩` disconnects the current guest and moves in the next one of the queue
    - `🔀` disconnects the current guest and moves in a random guest from the queue
    - `⏹` disconnects the current guest
    

