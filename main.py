from contextlib import nullcontext
import os
import discord
from os.path import join, dirname
from dotenv import load_dotenv
from rethinkdb import RethinkDB
from discord.ext import commands
from datetime import datetime

dotenv_path = join(dirname(__file__), '.env.dev')
load_dotenv(dotenv_path) # lire a partir du .env.dev
# load_dotenv()
r = RethinkDB()
conn = r.connect(host=os.getenv('DB_HOST_SERVER'), port=os.getenv('DB_HOST_PORT'), db=os.getenv('DB'))

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
    classement = ''
     
    async def on_ready(self):
        """quand le bot est lancé.
        """
        self.guild = self.get_guild(int(os.getenv("GUILD_ID")))
        self.classement = r.table("classement").order_by(r.desc('pts')).run(conn)
        for player in self.classement:
            for member in self.guild.members:
                if str(member.id) != player['id'] and not member.bot:
                    r.table('classement').insert({ 'id':str(member.id), 'pts':0 }).run(conn)
        await self.updates_bot()
        print(f'Logged on as {self.user}!')
        
    async def on_member_join(self,member):
        """ajoute un membre en DB s'il n'est pas un bot.

        Args:
            member (Member): discord.Member.
        """
        if not member.bot:
            r.table('classement').insert({ 'id':str(member.id), 'pts':0 }).run(conn)

    async def on_member_remove(self,member):
        """retire un membre de la DB.

        Args:
            member (Member): discord.Member.
        """
        r.table('classement').filter({'id':str(member.id)}).delete().run(conn)

    async def on_message(self, message):
        """détecte chaque message envoyé sur le serveur.

        Args:
            message (Message): discord.Message.
        """
        await self.battle(message)   

    async def battle(self, message):
        """trie par salon les tournois.

        Args:
            message (Message): discord.Message.
        """
        match message.channel.id:
            case 1100328720704745502:
                # Pokétwo
                # Freezing_Hell
                if 'Freezing_Hell' in str(message.author):
                    if ' won the battle!' in str(message.content):
                        r.table('classement').filter({'id':str(message.mentions[0].id)}).update({'pts':(r.row['pts']+self.pointToAdd)}).run(conn)
                        await self.updates_bot()
                    if ' has fled the battle!' in message.content:
                        r.table('classement').filter({'id':str(message.mentions[1].id)}).update({'pts':(r.row['pts']+self.pointToAdd)}).run(conn)
                        r.table('classement').filter({'id':str(message.mentions[0].id)}).update({'pts':(r.row['pts']-self.pointToRemove)}).run(conn)
                        await self.updates_bot()    
                        
    
    async def updates_bot(self):
        """joue toutes les fonctions en lien avec le classement et les roles.
        """
        start = datetime.now()
        self.classement = r.table('classement').order_by(r.desc('pts')).run(conn)
        await self.update_classement()
        await self.gestion_roles()
        end = datetime.now()
        elapsed = end - start
        print(f'Temps d\'exécution : {elapsed}ms')  

    async def update_classement(self):
        """mets a jour le classement.
        """
        channel = await self.fetch_channel('1100139943533228062')
        message = await channel.fetch_message('1100152446208180284')
        content = ''
        for i, member in enumerate(self.classement):
            i += 1
            content += f"{i} -> <@{int(member['id'])}> avec {member['pts']}\n"
        await message.edit(content=content)

    async def gestion_roles(self):
        """défini a partir du classement les roles a attribuer a chaque joueurs.
        """
        print('--------------------------------------------')
        for i, member in enumerate(self.classement):
            i += 1
            member = await self.guild.fetch_member(int(member['id']))
            # Role master
            if i == 1 and member.get_role(self.dict_roles_tournament['master']) == None:
                await self.update_roles(member,self.dict_roles_tournament['master'])
            # Role champion
            elif i >1 and i <= 5 and member.get_role(self.dict_roles_tournament['champion']) == None:
                await self.update_roles(member,self.dict_roles_tournament['champion'])
            # Role challenger
            elif i > 5 and i <= 20 and member.get_role(self.dict_roles_tournament['challenger']) == None:
                await self.update_roles(member,self.dict_roles_tournament['challenger'])
            # Role hobbyist
            elif i > 20 and i <= 50 and member.get_role(self.dict_roles_tournament['hobbyist']) == None:
                await self.update_roles(member,self.dict_roles_tournament['hobbyist'])
            # Role beginner
            elif i > 50 and i <=100 and member.get_role(self.dict_roles_tournament['beginner']) == None:
                await self.update_roles(member,self.dict_roles_tournament['beginner'])
            # Role non classé
            elif i >100 and member.get_role(self.dict_roles_tournament['non classé']) == None:
                await self.update_roles(member,self.dict_roles_tournament['non classé'])
        print('--------------------------------')
        print('INFO : traitement de \'update_roles()\' terminé ')
        print('--------------------------------')

    # update_roles( Member : membre, int : id a ajouter ) ## retireras tous les autres roles s'il y en a 
    async def update_roles(self,member,role_id_to_add):
        """attribue les roles et retire les aurtes roles 

        Args:
            member (Member): discord.Member.
            role_id_to_add (int): Integer, id du role a attribuer.
        """
        roles = []
        for role in self.dict_roles_tournament.values():
            if member.get_role(role) != None:
                roles.append(self.guild.get_role(role))
        await member.remove_roles(*roles)
        await member.add_roles(self.guild.get_role(role_id_to_add))

   
    

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.command()
async def test(ctx):
    await ctx.send("hello")

client = MyClient(intents=intents)
client.run(os.getenv("ACCESS_TOKEN"))