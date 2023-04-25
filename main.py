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
    guild = ''
    dict_roles_tournament = {
        'master':1100058331550322688,
        'champion':1100058273777979502,
        'challenger':1100058225941938267,
        'hobbyist':1100058110892191845,
        'beginner':1100058041572937810,
        'non classé':1100340506506051584
    }

    async def on_ready(self):
        self.guild = self.get_guild(int(os.getenv("GUILD_ID")))
        print(f"nom du serveur : {self.guild.name}")
        print(os.getenv("GUILD_ID"))
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
        if 'Pokétwo' in str(message.author):
            if message.channel.id == 1100328720704745502:
                print('hello')
                if ' won the battle!' in str(message.content):
                    r.table('classement').filter({'id':str(message.mentions[0].id)}).update({'pts':(r.row['pts']+self.pointToAdd)}).run(conn)
                if ' has fled the battle!' in message.content:
                    r.table('classement').filter({'id':str(message.mentions[1].id)}).update({'pts':(r.row['pts']+self.pointToAdd)}).run(conn)
                    r.table('classement').filter({'id':str(message.mentions[0].id)}).update({'pts':(r.row['pts']-self.pointToRemove)}).run(conn)
            classement = r.table('classement').order_by(r.desc('pts')).run(conn)
            await self.update_classement(classement)
            await self.gestion_roles(classement)


    async def update_classement(self,classement):
        channel = await self.fetch_channel('1100139943533228062')
        message = await channel.fetch_message('1100152446208180284')
        content = ''
        for i, member in enumerate(classement):
            i += 1
            content += f"{i} -> <@{int(member['id'])}> avec {member['pts']}\n"
        await message.edit(content=content)

    async def gestion_roles(self,classement):
        print('--------------------------------------------')
        for i, member in enumerate(classement):
            i += 1
            member = await self.guild.fetch_member(int(member['id']))
            # Role master
            if i == 1:
                await self.update_roles(member,self.dict_roles_tournament['master'])
                print(f"{member} aura le role {self.guild.get_role(self.dict_roles_tournament['master']).name}")
            # Role champion
            if i >1 and i <= 5:
                await self.update_roles(member,self.dict_roles_tournament['champion'])
                print(f"{member} aura le role {self.guild.get_role(self.dict_roles_tournament['champion']).name}")
            # Role challenger
            if i > 5 and i <= 20:
                await self.update_roles(member,self.dict_roles_tournament['challenger'])
                print(f"{member} aura le role {self.guild.get_role(self.dict_roles_tournament['challenger']).name}")
            # Role hobbyist
            if i > 20 and i <= 50:
                await self.update_roles(member,self.dict_roles_tournament['hobbyist'])
                print(f"{member} aura le role {self.guild.get_role(self.dict_roles_tournament['hobbyist']).name}")
            # Role beginner
            if i > 50 and i <=100:
                await self.update_roles(member,self.dict_roles_tournament['beginner'])
                print(f"{member} aura le role {self.guild.get_role(self.dict_roles_tournament['beginner']).name}")
            # Role non classé
            if i >100:
                await self.update_roles(member,self.dict_roles_tournament['non classé'])
                print(f"{member} aura le role {self.guild.get_role(self.dict_roles_tournament['non classé']).name}")

    # update_roles( Member : membre, int : id a ajouter ) ## retireras tous les autres roles s'il y en a 
    async def update_roles(self,member,role_id_to_add):
        for role in self.dict_roles_tournament.values():
            if member.get_role(role) != None:
                await member.remove_roles(self.guild.get_role(role))
        await member.add_roles(self.guild.get_role(role_id_to_add))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents=intents)
client.run(os.getenv("ACCESS_TOKEN"))