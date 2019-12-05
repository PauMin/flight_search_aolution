import os
import json
import ijson
import pandas as pd


def find_optimal_combination(f):
    # Get itinerary and fares to separate dictionaries
    itinerary = [*ijson.items(f, 'itinerary.item')]

    # Find variations
    variation = get_variations(f, itinerary)

    return variation['indexes']


def get_satisfactory_generator(f, itinerary):
    visited = []
    for route in itinerary:
        f.seek(0, 0)
        fares = ijson.items(f, 'fares.item')
        satisfactory = pd.DataFrame([fare for fare in fares if route in fare['routes']]).set_index('fid')

        # Exclude visited fares
        satisfactory.drop(visited, errors='ignore', inplace=True)

        # Exclude no show fares
        satisfactory.drop([i for i in no_show_generator(satisfactory, itinerary)], inplace=True)

        # Put weights on fares and sort them
        satisfactory['weight'] = [fare[1].price / len(fare[1].routes) for fare in satisfactory.iterrows()]
        satisfactory.sort_values(by=['weight'], inplace=True)

        # Drop duplicate fares with higher weight
        satisfactory["t_routes"] = satisfactory.routes.apply(lambda x: tuple(json.dumps(x)))
        satisfactory.drop_duplicates(subset='t_routes', keep='first', inplace=True)
        satisfactory.drop(['t_routes'], axis=1, inplace=True)

        visited.extend(satisfactory.index)

        yield satisfactory


def no_show_generator(df, itinerary):
    for i, fare in df.iterrows():
        result = pd.Series([route in itinerary for route in fare['routes']]).all()
        if ~result:
            yield i


def get_variations(f, itinerary):
    variations = []
    found = False

    satisfactory_generator = get_satisfactory_generator(f, itinerary)

    satisfactory = next(satisfactory_generator)

    variations.extend(
        [{
            'indexes': [fare[0]],
            'routes': fare[1].routes,
            'price': fare[1].price,
            'weight': fare[1].weight
        } for fare in satisfactory.iterrows()]
    )

    while not found:
        satisfactory = next(satisfactory_generator)
        fill = satisfactory.iloc[0]
        i_s = [i for i, variation in enumerate(variations) if not any(route in variation['routes'] for route in fill.routes)]

        for i in i_s:
            variations[i]['indexes'].append(satisfactory.first_valid_index())
            variations[i]['routes'].extend(fill.routes)
            variations[i]['price'] += fill.price
            variations[i]['weight'] = variations[0]['price'] / len(variations[0]['routes'])

        variations = sorted(variations, key=lambda i: i['weight'])

        if len(variations[0]['routes']) == len(itinerary):
            found = True

    return variations[0]


def main():
    with open(os.environ["DATA_FILE"], "r") as f:
        answer = find_optimal_combination(f)

    with open(os.environ["RESULT_FILE"], 'w') as f:
        f.write(json.dumps(answer))


if __name__ == "__main__":
    main()
