import numpy as np
from indicators import ssl_channels
def crossoverdetection(df):
    ssl60, hma_high60, hma_low60 = ssl_channels(df,60)
    ssl120, hma_high120, hma_low120 = ssl_channels(df,120)  
    crossover = np.zeros(len(df))
    for i in range(1, len(df)):
        if ssl60[i] == 1 and ssl120[i] == 1 and (ssl60[i-1] != 1 or ssl120[i-1] != 1):
            crossover[i] = 1
        elif ssl60[i] == -1 and ssl120[i] == -1 and (ssl60[i-1] != -1 or ssl120[i-1] != -1):
            crossover[i] = -1
    return crossover