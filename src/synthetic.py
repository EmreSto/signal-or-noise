import numpy as np
import pandas as pd
from arch import arch_model
def generate_garch_series(prices, n_simulations):
    returns = np.diff(np.log(prices))*100
    model = arch_model(returns, p=1 , q=1 , rescale = True)
    result = model.fit(disp='off')
    list_to_store = []
    for i in range(n_simulations):
        sim_data = model.simulate(result.params,nobs = len(returns))
        sim_returns = sim_data['data'] / 100
        sim_prices = prices.iloc[0] * np.exp(np.cumsum(sim_returns.values))
        sim_prices = pd.Series(sim_prices, index= prices.index[1:])
        list_to_store.append(sim_prices)
    return list_to_store


