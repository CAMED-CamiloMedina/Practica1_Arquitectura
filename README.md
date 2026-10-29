El archivo stats.txt y la carpeta que contiene todos los resultados de la simulaciones, tienen que estar en el mismo directorio que los archivos python.
Se compartirá un enlace de drive que tiene todas las simulaciones y un notebook con las observaciones y conclusiones.
https://drive.google.com/drive/folders/1jr9aO6b-pmvmo0FI0AjHfjpBl-aZAh8L?usp=sharing


Conclusiones:

Como se observa en los resultados anteriores, el mejor tiempo no lo tiene el que cuenta con la mayor contidad de unidades en lo parametros modificados, sino el que tiene un configuracion en especidico, en nuestro caso usamos como carga un audio MP3 y con una cache L3 de 1MiB, 6 unidades ALUs, 3 de Loads y 8 de Store, conseguimos el menor tiempo.

Aunque para el caso del menor consumo energetico y el menor EDP, la logica de tener la menor cantidad de unidades si se aplica, ya que para ambos casos el menor valore lo tiene la configuracion con una chache L3 de 1MiB, 1 unidade de ALUs, 1 de Loads y 1 de Store, esto tiene sentido, ya que al tener menos unidades que alimentar la energia necesaria disminuye, aunque el tiempo aumenta de procesado aumenta.

Como se menciono anteromente, tener una mayor cantidad de unidades en los parametros modificados no siempre resulta en el mejor rendimiento, esto no siempre es cierto, ya que si la carga de trabajo cambia y esta requiere de mas unidades, entonces obtenemos un buen resultado, pero si la carga de trabajo requiere menos unidades para trabajar, entonces la extras no seran utilizadas y no generaran una mejora en el rendimiento.

Como se observa en la grafica anterior de energia vs rendimiento, se puede observar que las configuraciones que tienen un mayor consumo de energia normalmente ofrecen un mejor rendimiento.
