import os
import json
import time
import pandas as pd


def find_optimal_combination(data):
    # Get itinerary and fares to separate dictionaries
    itinerary = data['itinerary']
    fares = data['fares']

    # Convert data frames
    df_fares = pd.DataFrame.from_dict(fares).set_index('fid')

    # Exclude no show fares
    no_show = [i for i in no_show_generator(df_fares, itinerary)]
    df_fares.drop(no_show, inplace=True)

    # Put weights on fares and sort them
    df_fares['weight'] = [len(fare[1].routes) / fare[1].price for fare in df_fares.iterrows()]
    df_fares.sort_values(by=['weight'], inplace=True)

    # Drop duplicate fares with higher weight
    df_fares["t_routes"] = df_fares.routes.apply(lambda x: tuple(json.dumps(x)))
    df_fares.drop_duplicates(subset='t_routes', keep='first')

    start = time.time()
    # Find variations
    variations = get_variations(df_fares, itinerary)
    finish = time.time()

    print(finish - start)

    # Get cheapest variation
    profitable = min(variations, key=lambda x: x['price'])

    return profitable['indexes']


def no_show_generator(df, itinerary):
    for i, fare in df.iterrows():
        result = pd.Series([route in itinerary for route in fare['routes']]).all()
        if ~result:
            yield i


def get_variations(df, itinerary):
    left_fares = df.copy()
    variations = []

    for route in itinerary:
        satisfactory = left_fares[[route in fare for fare in left_fares.routes]]
        left_fares.drop(satisfactory.index, inplace=True)

        if not variations:
            variations.extend(
                [{
                    'indexes': [fare[0]],
                    'routes': fare[1].routes,
                    'price': fare[1].price
                } for fare in satisfactory.iterrows()]
            )
            continue

        i_s = [i for i, variation in enumerate(variations) if route not in variation['routes']]
        fill = satisfactory.iloc[0]
        for i in i_s:
            variations[i]['indexes'].append(satisfactory.first_valid_index())
            variations[i]['routes'].extend(fill.routes)
            variations[i]['price'] += fill.price

    return variations


def main():
    with open(os.environ["DATA_FILE"], "r") as f:
        data = json.loads(f.read())

    answer = find_optimal_combination(data)

    with open(os.environ["RESULT_FILE"], 'w') as f:
        f.write(json.dumps(answer))


if __name__ == "__main__":
    main()
