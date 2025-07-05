import random
import unicodedata

# import discord
# from discord.ext import commands
# import requests
# import secrets # archivo secrets.py

def quitar_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')

def crear_baraja():
    baraja = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
    random.shuffle(baraja)
    return baraja

def calcular_puntuacion(mano):
    total = sum(mano)
    num_aces = mano.count(11)
    while total > 21 and num_aces:
        total -= 10
        num_aces -= 1
    return total

def mostrar_puntuacion(mano):
    total = sum(mano)
    if 11 in mano:
        total_1 = total
        num_aces = mano.count(11)
        while total_1 > 21 and num_aces:
            total_1 -= 10
            num_aces -= 1
        if total_1 != total:
            return f"{total_1}/{total}"
    return f"{total}"

def mostrar_mano(mano):
    return [("A" if carta == 11 else carta) for carta in mano]

def jugar_jugador_y_dealer(jugador, baraja, saldo):
    while True:
        try:
            apuesta = int(input(f"\n{jugador}, tu saldo es {saldo} monedas. ¿Cuánto deseas apostar? (1 - {saldo}): "))
            if 1 <= apuesta <= saldo:
                break
            else:
                print("Apuesta no válida.")
        except:
            print("Ingresa un número válido.")

    saldo -= apuesta

    mano_jugador = [baraja.pop(), baraja.pop()]
    mano_dealer = [baraja.pop(), baraja.pop()]

    print(f"\n{jugador}, tus cartas son: {mostrar_mano(mano_jugador)} (Puntuación: {mostrar_puntuacion(mano_jugador)})")
    print(f"El dealer muestra: {mostrar_mano([mano_dealer[0]])} y una carta oculta.")

    blackjack_jugador = calcular_puntuacion(mano_jugador) == 21
    blackjack_dealer = calcular_puntuacion(mano_dealer) == 21

    if blackjack_jugador or blackjack_dealer:
        print(f"\nEl dealer revela su mano: {mostrar_mano(mano_dealer)} (Puntuación: {mostrar_puntuacion(mano_dealer)})")

        if blackjack_jugador and blackjack_dealer:
            print("Ambos tienen Blackjack. Es un empate.")
            saldo += apuesta
        elif blackjack_jugador:
            print("¡Tienes Blackjack! Ganaste 1.5x tu apuesta.")
            saldo += int(apuesta * 2.5)
        else:
            print("El dealer tiene Blackjack. Pierdes la apuesta.")
        return {
            jugador: {
                'mano': [mano_jugador],
                'resultados': [],
                'apuesta': apuesta,
                'saldo': saldo,
                'doblar': False,
                'mano_dealer': mano_dealer,
                'terminado': True
            }
        }

    return jugar_mano(jugador, baraja, saldo, apuesta, mano_jugador, mano_dealer)

def jugar_mano(jugador, baraja, saldo, apuesta, mano_jugador, mano_dealer):
    doblar = False

    if len(mano_jugador) == 2 and calcular_puntuacion(mano_jugador) in [9, 10, 11]:
        respuesta = input(f"{jugador}, ¿quieres doblar tu apuesta? (Sí/No): ").strip().lower()
        if quitar_tildes(respuesta) in ["si", "s"] and saldo >= apuesta:
            saldo -= apuesta
            apuesta *= 2
            mano_jugador.append(baraja.pop())
            print(f"Tu nueva mano: {mostrar_mano(mano_jugador)} (Puntuación: {mostrar_puntuacion(mano_jugador)})")
            doblar = True

    manos_jugadores = [mano_jugador]
    if len(mano_jugador) == 2 and mano_jugador[0] == mano_jugador[1]:
        respuesta = input(f"{jugador}, ¿quieres dividir las cartas? (Sí/No): ").strip().lower()
        if quitar_tildes(respuesta) in ["si", "s"] and saldo >= apuesta:
            saldo -= apuesta
            apuesta *= 2
            mano1 = [mano_jugador[0], baraja.pop()]
            mano2 = [mano_jugador[1], baraja.pop()]
            manos_jugadores = [mano1, mano2]
            print(f"Mano 1: {mostrar_mano(mano1)}, Mano 2: {mostrar_mano(mano2)}")

    resultados = []
    for i, mano in enumerate(manos_jugadores):
        while True:
            puntuacion = calcular_puntuacion(mano)
            print(f"Mano {i+1}: {mostrar_mano(mano)} (Puntuación: {mostrar_puntuacion(mano)})")
            if puntuacion > 21:
                print("Te pasaste. Pierdes esta mano.")
                resultados.append("perdió")
                break

            decision = input(f"{jugador}, ¿Pedir o Plantarse? ").strip().lower()
            if quitar_tildes(decision) == "pedir":
                mano.append(baraja.pop())
            elif quitar_tildes(decision) == "plantarse":
                resultados.append("jugó")
                break
            else:
                print("Opción no válida.")

    return {
        jugador: {
            'mano': manos_jugadores,
            'resultados': resultados,
            'apuesta': apuesta,
            'saldo': saldo,
            'doblar': doblar,
            'mano_dealer': mano_dealer,
            'terminado': False
        }
    }

def jugar_partida(jugadores, saldo_inicial):
    baraja = crear_baraja()
    resultados = {}

    for jugador in jugadores:
        resultado_jugador = jugar_jugador_y_dealer(jugador, baraja, saldo_inicial)
        resultados.update(resultado_jugador)

    for jugador, info in resultados.items():
        if info['terminado']:
            continue

        mano_dealer = info['mano_dealer']
        print(f"\nEl dealer revela su mano: {mostrar_mano(mano_dealer)} (Puntuación: {mostrar_puntuacion(mano_dealer)})")
        while calcular_puntuacion(mano_dealer) < 17:
            mano_dealer.append(baraja.pop())
            print(f"El dealer pide carta: {mostrar_mano(mano_dealer)} (Puntuación: {mostrar_puntuacion(mano_dealer)})")

        puntuacion_dealer = calcular_puntuacion(mano_dealer)
        saldo = info['saldo']
        apuesta = info['apuesta']

        resumen = []

        for i, resultado in enumerate(info['resultados']):
            mano = info['mano'][i]
            puntuacion_jugador = calcular_puntuacion(mano)
            resultado_texto = ""
            cambio_saldo = 0

            if resultado == "perdió":
                resultado_texto = f"✖ Mano {i+1}: Perdiste"
                cambio_saldo = -apuesta
            elif puntuacion_dealer > 21 or puntuacion_jugador > puntuacion_dealer:
                resultado_texto = f"✔ Mano {i+1}: Ganaste"
                if info['doblar']:
                    cambio_saldo = int(apuesta * 2 * 1.5)
                else:
                    cambio_saldo = apuesta
            elif puntuacion_jugador == puntuacion_dealer:
                resultado_texto = f"➖ Mano {i+1}: Empate"
                cambio_saldo = apuesta
            else:
                resultado_texto = f"✖ Mano {i+1}: Perdiste"
                cambio_saldo = -apuesta

            saldo += cambio_saldo
            resumen.append((resultado_texto, cambio_saldo))

        # Mostrar resumen al final
        print("\n🧾 Resumen de tus manos:")
        for texto, cambio in resumen:
            signo = "+" if cambio > 0 else ""
            print(f"{texto} → {signo}{cambio} monedas")

        resultados[jugador]['saldo'] = max(0, saldo)

    return resultados


def juego_blackjack():
    jugadores = ["Jugador 1"]
    saldos = {jugador: 5000 for jugador in jugadores}

    while True:
        print("\n🎲 Nueva ronda de Blackjack 🎲")
        resultados = jugar_partida(jugadores, saldo_inicial=saldos["Jugador 1"])

        for jugador in jugadores:
            saldos[jugador] = resultados[jugador]['saldo']
            print(f"{jugador} ahora tiene un saldo de {saldos[jugador]} monedas.")

        if saldos["Jugador 1"] <= 0:
            print(f"\n{jugadores[0]}, te has quedado sin saldo. Fin del juego.")
            break

        respuesta = input(f"\n{jugadores[0]}, ¿quieres jugar otra ronda? (Sí/No): ").strip().lower()
        if quitar_tildes(respuesta) not in ["si", "s"]:
            print(f"\nGracias por jugar, {jugadores[0]}. Te retiras con {saldos[jugadores[0]]} monedas.")
            break

# Iniciar el juego
juego_blackjack()