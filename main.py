from contextlib import nullcontext
import os
import discord
from dotenv import load_dotenv
from rethinkdb import RethinkDB

load_dotenv()
r = RethinkDB()
conn = r.connect(host='localhost', port=28015, db='pokemon')

class MyClient(discord.Client):

    pointToAdd = 10
    pointToRemove = 20

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_member_join(self,member):
        print(f"{member}::{member.id} a rejoint le serveur")

        r.table('classement').insert({ 'id':str(member.id), 'pts':0 }).run(conn)

    async def on_member_remove(self,member):
        print(f"{member}::{member.id} a quitté le serveur")
        r.table('classement').filter({'id':str(member.id)}).delete().run(conn)

    async def on_message(self, message):
        # Pokétwo
        # Freezing_Hell
        if 'Freezing_Hell' in str(message.author):
            if ' won the battle!' in str(message.content):
                id = message.mentions[0].id
                r.table('classement').filter({'id':id}).update({'pts':(r.row['pts']+self.pointToAdd)}).run(conn)
                classement = r.table('classement').order_by(r.desc('pts')).run(conn)
                channel = await self.fetch_channel('1100139943533228062')
                message = await channel.fetch_message('1100152446208180284')
                content = ''
                for i, member in enumerate(classement):
                    i += 1
                    content += f"{i} -> <@{int(member['id'])}> avec {member['pts']}\n"
                await message.edit(content=content)
            ##  fuite  ##  perte de point pour le fuyard en fonction du classement de l'adversaire
            ##  ++PointPerdu if --ClassmentAdversaire  ##
            if ' has fled the battle!' in message.content:
                id1 = message.mentions[0].id
                r.table('classement').filter({'id':id1}).update({'pts':(r.row['pts']+self.pointToAdd)}).run(conn)
                id2 = message.mentions[1].id
                r.table('classement').filter({'id':id2}).update({'pts':(r.row['pts']+self.pointToRemove)}).run(conn)
                #self.updateClassement()        

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents=intents)
client.run(os.getenv("ACCESS_TOKEN"))