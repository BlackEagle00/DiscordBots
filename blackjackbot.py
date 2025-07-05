import discord, random, unicodedata
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

TOKEN = "TOKEN"

def crear_baraja():
    baraja = [2,3,4,5,6,7,8,9,10,10,10,10,11]*4
    random.shuffle(baraja)
    return baraja

def calcular_puntuacion(mano):
    total = sum(mano)
    aces = mano.count(11)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def mostrar_mano(mano):
    return [("A" if c == 11 else c) for c in mano]

def mostrar_puntuacion(mano):
    total = sum(mano)
    if 11 in mano:
        total_1 = total
        aces = mano.count(11)
        while total_1 > 21 and aces:
            total_1 -= 10
            aces -= 1
        if total_1 != total:
            return f"{total_1}/{total}"
    return f"{total}"

class BlackjackView(View):
    def __init__(self, interaction, apuesta, baraja, manos, mano_dealer):
        super().__init__(timeout=120)
        self.interaction = interaction
        self.baraja = baraja
        self.manos = manos  # lista de manos (1 o 2 si se divide)
        self.mano_dealer = mano_dealer
        self.apuesta = apuesta
        self.resultado = []
        self.turno = 0  # para manejar cuál mano está jugando
        self.doblado = [False] * len(manos)

    async def actualizar_mensaje(self):
        mano = self.manos[self.turno]
        texto = (
            f"🃏 Mano {self.turno+1}: {mostrar_mano(mano)} ({mostrar_puntuacion(mano)})\n"
            f"El dealer muestra: {mostrar_mano([self.mano_dealer[0]])}\n"
        )
        await self.interaction.edit_original_response(content=texto, view=self)

    async def terminar_mano(self, mensaje):
        self.resultado.append(mensaje)
        self.turno += 1
        if self.turno >= len(self.manos):
            self.stop()
        else:
            await self.actualizar_mensaje()

    @discord.ui.button(label="Pedir", style=discord.ButtonStyle.primary)
    async def pedir(self, i:discord.Interaction, b:Button):
        mano = self.manos[self.turno]
        mano.append(self.baraja.pop())
        puntos = calcular_puntuacion(mano)
        if puntos > 21:
            await i.response.send_message(f"🟥 Te pasaste con {mostrar_mano(mano)} ({puntos})", ephemeral=True)
            await self.terminar_mano("perdió")
        else:
            await self.actualizar_mensaje()
            await i.response.defer()

    @discord.ui.button(label="Plantarse", style=discord.ButtonStyle.secondary)
    async def plantarse(self, i:discord.Interaction, b:Button):
        await self.terminar_mano("jugó")
        await i.response.defer()

    @discord.ui.button(label="Doblar", style=discord.ButtonStyle.success)
    async def doblar(self, i:discord.Interaction, b:Button):
        mano = self.manos[self.turno]
        if len(mano) != 2:
            await i.response.send_message("Solo puedes doblar con dos cartas.", ephemeral=True)
            return
        mano.append(self.baraja.pop())
        self.apuesta *= 2
        self.doblado[self.turno] = True
        puntos = calcular_puntuacion(mano)
        await i.response.send_message(f"Doblaste. Tu mano es {mostrar_mano(mano)} ({puntos})", ephemeral=True)
        if puntos > 21:
            await self.terminar_mano("perdió")
        else:
            await self.terminar_mano("jugó")

    @discord.ui.button(label="Dividir", style=discord.ButtonStyle.danger)
    async def dividir(self, i:discord.Interaction, b:Button):
        mano = self.manos[self.turno]
        if len(mano) == 2 and mano[0] == mano[1]:
            self.manos = [
                [mano[0], self.baraja.pop()],
                [mano[1], self.baraja.pop()]
            ]
            self.doblado = [False, False]
            self.turno = 0
            await i.response.send_message("Cartas divididas.", ephemeral=True)
            await self.actualizar_mensaje()
        else:
            await i.response.send_message("Solo puedes dividir si tienes dos cartas iguales.", ephemeral=True)

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user}")

@bot.tree.command(name="blackjack", description="Juega una ronda de Blackjack")
async def blackjack(interaction: discord.Interaction):
    baraja = crear_baraja()
    apuesta = 1000
    mano_jugador = [baraja.pop(), baraja.pop()]
    mano_dealer = [baraja.pop(), baraja.pop()]

    view = BlackjackView(interaction, apuesta, baraja, [mano_jugador], mano_dealer)

    await interaction.response.send_message(
        f"Tu mano: {mostrar_mano(mano_jugador)} ({mostrar_puntuacion(mano_jugador)})\n"
        f"El dealer muestra: {mostrar_mano([mano_dealer[0]])}",
        view=view
    )
    await view.wait()

    resultados = view.resultado
    manos = view.manos
    doblado = view.doblado

    # Dealer juega solo si el jugador no se pasó en todas las manos
    jugar_dealer = any(r == "jugó" for r in resultados)
    if jugar_dealer:
        while calcular_puntuacion(mano_dealer) < 17:
            mano_dealer.append(baraja.pop())

    respuesta_final = f"\n🃏 Dealer: {mostrar_mano(mano_dealer)} ({mostrar_puntuacion(mano_dealer)})\n"
    total = 0

    for i, resultado in enumerate(resultados):
        puntos_j = calcular_puntuacion(manos[i])
        puntos_d = calcular_puntuacion(mano_dealer)
        apuesta_final = apuesta * 2 if doblado[i] else apuesta

        if resultado == "perdió":
            cambio = -apuesta_final
            mensaje = f"❌ Mano {i+1}: Te pasaste. Pierdes {abs(cambio)} monedas."
        elif puntos_d > 21 or puntos_j > puntos_d:
            cambio = apuesta_final
            mensaje = f"✅ Mano {i+1}: Ganaste {cambio} monedas."
        elif puntos_j == puntos_d:
            cambio = 0
            mensaje = f"➖ Mano {i+1}: Empate. No ganas ni pierdes."
        else:
            cambio = -apuesta_final
            mensaje = f"❌ Mano {i+1}: Pierdes contra el dealer. Pierdes {abs(cambio)} monedas."

        total += cambio
        respuesta_final += mensaje + "\n"

    await interaction.followup.send(respuesta_final + f"\n💰 Resultado total: {total} monedas")

bot.run(TOKEN)
