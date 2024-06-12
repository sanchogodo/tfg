import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import threading
import queue
import getpass

# ConfiguraciÃ³n del puerto serie
ser = serial.Serial('COM8', 9600, timeout=1)

# ConfiguraciÃ³n de las grÃ¡ficas
fig = plt.figure(figsize=(10, 6))
ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212)

# Ajustar lÃ­mites de las subfiguras
ax1.set_position([0.1, 0.5, 0.8, 0.4])
ax2.set_position([0.1, 0.1, 0.8, 0.4])

# Listas para almacenar los datos
datos_x, datos_y = [], []
datos_sensorA = []
datos_sensorB = []

# Inicializar los scatter plots
scatterA = ax1.scatter([], [], c=[], cmap='viridis', marker='o')
scatterB = ax2.scatter([], [], c=[], cmap='viridis', marker='o')

# Inicializar las barras de color
cbarA = fig.colorbar(scatterA, ax=ax1, label='Sensor A (lux)')
cbarB = fig.colorbar(scatterB, ax=ax2, label='Sensor B (lux)')

# Texto para el contador de datos
texto = fig.text(0.02, 0.5, '', horizontalalignment='left', verticalalignment='center')

# AÃ±adir etiquetas de ejes
ax1.set_xlabel('Eje X (cm)')
ax1.set_ylabel('Eje Y (cm)')
ax2.set_xlabel('Eje X (cm)')
ax2.set_ylabel('Eje Y (cm)')

# Variable para detener la recepciÃ³n de datos
recepcion_datos = True

# Cola para almacenar los comandos
cola_comandos = queue.Queue()

# Variables para rastrear la Ãºltima posiciÃ³n
ultima_x, ultima_y = None, None
contador_datos = 0

def actualizar(frame):
    global recepcion_datos, ultima_x, ultima_y, contador_datos
    if recepcion_datos:
        linea = ser.readline().decode('utf-8').strip()
        if linea:
            try:
                x, y, sensorA, sensorB = map(float, linea.split(','))
                print(f'Datos recibidos: x={x}, y={y}, sensorA={sensorA}, sensorB={sensorB}')  # Mostrar los datos recibidos

                # Solo incrementar el contador si la posiciÃ³n es distinta de la anterior
                if (x, y) != (ultima_x, ultima_y):
                    contador_datos += 1
                    ultima_x, ultima_y = x, y

                    datos_x.append(x)
                    datos_y.append(y)
                    datos_sensorA.append(sensorA)
                    datos_sensorB.append(sensorB)

                    # Calcular los nuevos lÃ­mites de color basados en los datos actuales
                    min_sensorA = min(datos_sensorA)
                    max_sensorA = max(datos_sensorA)
                    min_sensorB = min(datos_sensorB)
                    max_sensorB = max(datos_sensorB)

                    vmin = min(min_sensorA, min_sensorB)
                    vmax = max(max_sensorA, max_sensorB)

                    # Actualizar los datos del scatter plot del sensor A
                    scatterA.set_offsets(np.c_[datos_x, datos_y])
                    scatterA.set_array(np.array(datos_sensorA))
                    scatterA.set_clim(vmin=vmin, vmax=vmax)  # Rango dinÃ¡mico de colores

                    # Actualizar los datos del scatter plot del sensor B
                    scatterB.set_offsets(np.c_[datos_x, datos_y])
                    scatterB.set_array(np.array(datos_sensorB))
                    scatterB.set_clim(vmin=vmin, vmax=vmax)  # Rango dinÃ¡mico de colores

                    # Configurar lÃ­mites de los ejes para mejor visualizaciÃ³n
                    ax1.set_xlim(min(datos_x) - 1, max(datos_x) + 1)
                    ax1.set_ylim(min(datos_y) - 1, max(datos_y) + 1)
                    ax2.set_xlim(min(datos_x) - 1, max(datos_x) + 1)
                    ax2.set_ylim(min(datos_y) - 1, max(datos_y) + 1)

                    # Actualizar las barras de color
                    cbarA.update_normal(scatterA)
                    cbarB.update_normal(scatterB)

                    # AÃ±adir lÃ­neas de rejilla
                    ax1.grid(True)
                    ax2.grid(True)

                    # Actualizar el contador de datos
                    texto.set_text(f'Datos incluidos: {contador_datos}')

            except ValueError:
                pass

        # Enviar comandos al vehÃ­culo
        while not cola_comandos.empty():
            comando = cola_comandos.get()
            ser.write(comando.encode())

def detener_datos(event):
    global recepcion_datos
    if event.key == 'E':
        recepcion_datos = False
        print("RecepciÃ³n de datos detenida.")
        # Guardar la grÃ¡fica
        plt.savefig('grafica_datos_sensores.png')
        print("GrÃ¡fica guardada como 'grafica_datos_sensores.png'.")

# FunciÃ³n para recibir comandos del usuario
def recibir_comandos():
    while True:
        comando = getpass.getpass(prompt='')  # Oculta la entrada del usuario
        cola_comandos.put(comando)

# Crear una hebra para recibir comandos del usuario
hebra_comandos = threading.Thread(target=recibir_comandos)
hebra_comandos.daemon = True
hebra_comandos.start()

# Enlace de eventos para detener la recepciÃ³n de datos
fig.canvas.mpl_connect('key_press_event', detener_datos)

# AnimaciÃ³n de las grÃ¡ficas
ani = animation.FuncAnimation(fig, actualizar, interval=1000)

plt.tight_layout()
plt.show()

# Cierre del puerto serie al finalizar
ser.close()