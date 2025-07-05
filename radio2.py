import discord
from discord.ext import commands
import requests
import yt_dlp as youtube_dl
import asyncio

# Configuración del bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Crear un objeto para manejar la conexión al canal de voz
voice_client = None

# Función para obtener la URL de transmisión de la estación de radio desde la API de Radio Garden
def obtener_url_radio(nombre_estacion):
    # Usar el endpoint oficial de Radio Garden para obtener la estación
    url_api = f"https://radio.garden/api/ara/content/radios/online/{nombre_estacion}"
    try:
        response = requests.get(url_api)
        if response.status_code == 200:
            data = response.json()
            if "live" in data:
                # Extraemos la URL de la transmisión en vivo
                stream_url = data["live"]["url"]
                return stream_url
            else:
                print("No se pudo encontrar la URL de transmisión.")
                return None
        else:
            print(f"Error al hacer la petición: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return None

# Función para reproducir la radio en el canal de voz
async def reproducir_radio(ctx, stream_url):
    global voice_client
    try:
        if voice_client and voice_client.is_playing():
            await ctx.send("Ya estoy reproduciendo otra estación de radio.")
            return

        # Reproducir el stream en el canal de voz
        ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioquality': 1,
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'quiet': True,
            'logtostderr': False
        }

        # Usamos yt-dlp para obtener la URL del stream de audio
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(stream_url, download=False)
            url2 = info_dict['formats'][0]['url']

        # Conectamos al canal de voz
        if not voice_client or not voice_client.is_connected():
            voice_channel = ctx.author.voice.channel
            voice_client = await voice_channel.connect()

        # Reproducir la transmisión en vivo
        voice_client.play(discord.FFmpegPCMAudio(url2), after=lambda e: print(f'Error: {e}') if e else None)
        await ctx.send(f"Reproduciendo la estación de radio: {stream_url}")
        
    except Exception as e:
        print(f"Error al reproducir la radio: {e}")
        await ctx.send("Hubo un problema al intentar reproducir la radio.")

# Comando para unirse al canal de voz y reproducir la radio
@bot.command(name='reproducir')
async def reproducir(ctx, nombre_estacion: str):
    # Obtener la URL de la estación de radio
    stream_url = obtener_url_radio(nombre_estacion)
    if stream_url:
        await reproducir_radio(ctx, stream_url)
    else:
        await ctx.send("No se pudo encontrar la estación de radio.")

# Comando para detener la reproducción
@bot.command(name='detener')
async def detener(ctx):
    global voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await ctx.send("Se detuvo la reproducción.")
    else:
        await ctx.send("No hay ninguna radio reproduciéndose.")

# Comando para hacer que el bot se desconecte del canal de voz
@bot.command(name='salir')
async def salir(ctx):
    global voice_client
    if voice_client:
        await voice_client.disconnect()
        voice_client = None
        await ctx.send("Desconectado del canal de voz.")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")

# Comando para listar todas las estaciones de radio disponibles (opcional)
@bot.command(name='estaciones')
async def estaciones(ctx):
    # Endpoint para obtener todas las estaciones de radio
    url_api = "https://radio.garden/api/ara/content/radios/online"
    try:
        response = requests.get(url_api)
        if response.status_code == 200:
            data = response.json()
            # Imprimir las primeras 10 estaciones de radio disponibles
            estaciones = data[:10]  # Limitar la cantidad para no hacer spam
            estaciones_nombres = [estacion['name'] for estacion in estaciones]
            await ctx.send("Estaciones disponibles: \n" + "\n".join(estaciones_nombres))
        else:
            await ctx.send("No pude obtener las estaciones de radio.")
    except Exception as e:
        print(f"Ocurrió un error al obtener las estaciones: {e}")
        await ctx.send("Hubo un problema al obtener las estaciones.")

# Iniciar el bot con el token
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

bot.run('TU_TOKEN_AQUI')
