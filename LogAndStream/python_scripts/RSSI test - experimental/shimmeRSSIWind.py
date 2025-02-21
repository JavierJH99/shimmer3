import bluetooth
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Lista de direcciones MAC de dispositivos Bluetooth a rastrear
macIDs = ['D8:47:8F:04:BC:A6']
numDev = len(macIDs)

print(f"Number of devices: {numDev}")

timeStamp = [[] for _ in range(numDev)]
rssi = [[] for _ in range(numDev)]
data = [[] for _ in range(numDev)]

# Función para escanear dispositivos Bluetooth y obtener su RSSI
def scan_devices():
    nearby_devices = bluetooth.discover_devices(duration=5, lookup_names=True, flush_cache=True)
    results = []
    for addr, name in nearby_devices:
        print(f"Found: {name} - {addr}")
        results.append((addr, name, None))  # RSSI no disponible en PyBluez para Windows
    return results

# Función para manejar el cierre de la ventana y guardar datos
def handle_close(evt):
    print("Testing done!")

    if not os.path.exists("./data"):
        os.makedirs("./data", exist_ok=True)

    for i in range(numDev):
        filename = f"data/RSSI_{macIDs[i].replace(':', '')}_{time.strftime('%d-%m-%Y_%H.%M')}.txt"
        with open(filename, 'w') as f:
            for d in data[i]:
                f.write(", ".join(map(str, d)) + "\n")

    print("File saved")

# Configuración de la gráfica en tiempo real
fig = plt.figure()
fig.canvas.mpl_connect('close_event', handle_close)
ax = [fig.add_subplot(numDev, 1, i + 1) for i in range(numDev)]

for i, a in enumerate(ax):
    a.set_title(macIDs[i])
    a.set_ylabel('RSSI in dBm')

# Función para actualizar la animación en la gráfica
def animate(i):
    results = scan_devices()
    
    for addr, name, rssi_value in results:
        for j in range(numDev):
            if macIDs[j] == addr:
                rssi[j].append(rssi_value if rssi_value else -99)  # PyBluez no obtiene RSSI en Windows
                timeStamp[j].append(time.strftime("%H:%M:%S"))
                data[j].append([timeStamp[j][-1], rssi[j][-1]])

    for k in range(numDev):
        if len(rssi[k]) > 1:
            print(data[k][-1])
            ax[k].clear()
            ax[k].set_title(macIDs[k])
            ax[k].set_ylabel('RSSI in dBm')
            ax[k].plot(range(len(rssi[k])), rssi[k])

# Iniciar animación en tiempo real
try:
    ani = animation.FuncAnimation(fig, animate, interval=5000)  # Escaneo cada 5 segundos
    plt.show()
except KeyboardInterrupt:
    print("Interrupted!")
    plt.close()