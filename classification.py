def classify_duracion(minutos):
    if minutos < 16:
        return "roca suave"
    elif minutos < 24:
        return "roca media"
    elif minutos < 40:
        return "roca dura"
    else:
        return "roca muy dura"


def hardness_index(T):
    if T < 0:
        return 0.0
    elif T <= 16:
        return 25.0 * (T / 16.0)
    elif T <= 24:
        return 25.0 + 25.0 * ((T - 16.0) / 8.0)
    elif T <= 40:
        return 50.0 + 25.0 * ((T - 24.0) / 16.0)
    elif T <= 60:
        return 75.0 + 25.0 * ((T - 40.0) / 20.0)
    else:
        return 100.0