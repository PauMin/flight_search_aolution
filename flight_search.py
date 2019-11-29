import os
import json
import time
import threading
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

    start = time.time()
    # Find variations
    variations = get_variations(df_fares, itinerary)
    finish = time.time()

    print(finish - start)

    # Get cheapest variation
    profitable = min(variations, key=lambda x: x['price'])

    return profitable['index']


def no_show_generator(df, itinerary):
    for i, fare in df.iterrows():
        result = pd.Series([route in itinerary for route in fare['routes']]).all()
        if ~result:
            yield i


def route_generator(routes):
    for route in routes:
        yield route


def satisfactory_generator(left_fares, route):
    for index, fare in left_fares.iterrows():
        if route in fare['routes']:
            yield {
                'price': fare['price'],
                'routes': fare['routes'],
                'index': index
            }


def get_variations(df, itinerary):
    routes = route_generator(itinerary.copy())
    left_fares = df.copy()
    variations = []

    def fare_thread(t_fare, t_route):
        for variation in variations:
            if t_route not in variation['routes']:
                variation['price'] += t_fare['price']
                variation['routes'] += t_fare['routes']
                if type(variation['index']) == list:
                    variation['index'].append(t_fare['index'])
                else:
                    variation['index'] = [variation['index'], t_fare['index']]

    for route in routes:
        satisfactory = satisfactory_generator(left_fares, route)
        threads = []

        if not variations:
            variations.extend(satisfactory)
            continue

        for fare in satisfactory:
            x = threading.Thread(target=fare_thread, args=(fare, route,))
            threads.append(x)
            x.start()
            left_fares.drop(fare['index'], inplace=True)

        for index, thread in enumerate(threads):
            thread.join()

    return variations


def main():
    with open(os.environ["DATA_FILE"], "r") as f:
        data = json.loads(f.read())

    answer = find_optimal_combination(data)

    with open(os.environ["RESULT_FILE"], 'w') as f:
        f.write(json.dumps(answer))


if __name__ == "__main__":
    main()
